"""
stolen from isobar
"""
import time
import threading
import queue
import logging

try:
    import rtmidi
except:
    print("rtmidi not found, no MIDI support available.")
    exit(0)

from rtmidi.midiconstants import *

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

class MidiPort:
    """
    common between MidiInput and MidiOutput
    """
    def __init__(self):
        self.ports = None
        self.port_name = None

    def get_port_names(self):
        self.ports = self.midi.get_ports()
        if len(self.ports) == 0:
            raise Exception("No MIDI in ports found")
        return self.ports

    def open_port(self, port_name):
        if self.ports is None:
            self.get_port_names()

        if self.port_name is not None:
            self.close_port()

        port_index = None
        for index, name in enumerate(self.ports):
            log.info(f"MIDI port: {name}")
            if port_name == name:
                log.info(f"Found desired MIDI port: {name}")
                port_index = index

        if port_index is None:
            raise Exception(f'Cannot find desired port named {name}')

        try:
            self.midi.open_port(port_index)
        except:
            raise Exception(f'Cannot open port {name}')

        self.port_name = self.midi.get_port_name(port_index)
        log.info(f"Opened MIDI port: {self.port_name}")

    def close_port(self):
        self.midi.close_port()
        self.port_name = None


class MidiInput(MidiPort):
    def __init__(self, q_size_limit=1024, ignore_clock=True):
        self.midi = rtmidi.MidiIn(queue_size_limit=q_size_limit)

        if ignore_clock == False:
            self.midi.ignore_types(timing = False) #don't ignore MIDI clock messages

        self.note_callback = None

        self.clock_callback = None
        self.clock_midiin = None
        self.clock_delta_time = 0.0   # the time between clock msgs
        self.clock_counts = 0

        self.control_callback = None
        self.control_data = None

    def register_note_callback(self, callback, clock_midiin):
        self.note_callback = callback
        self.clock_midiin = clock_midiin

    def register_clock_callback(self, callback, data=None):
        self.clock_callback = callback
        self.clock_data = data

    def register_control_callback(self, callback, data=None):
        self.control_callback = callback
        self.control_data = data

    def get_tick(self):
        return self.clock_counts

    def callback(self, msg_dt, data):
        message = msg_dt[0]
        data_type = message[0]

        if self.clock_callback is not None:
            if data_type == TIMING_CLOCK:
                self.clock_delta_time = msg_dt[1]   # the time between clock msgs
                self.clock_counts += 1           # number of clock msgs since inception
                self.clock_callback(self.clock_counts, self.clock_data)
            return 

        if self.note_callback is not None:
            if data_type is NOTE_OFF or data_type is NOTE_ON:
                log.info(f"{self.port_name} - Note In: {message}")
                self.note_callback(message, self.clock_midiin)

        if self.control_callback is not None:
            if data_type is CONTROL_CHANGE:
                log.info(f"{self.port_name} - Control: {message}")
                self.control_callback(message[1], message[2])

    def run(self):
        self.midi.set_callback(self.callback)

    def __destroy__(self):
        del self.midi


class MidiOutput(MidiPort):
    def __init__(self):
        self.midi = rtmidi.MidiOut()
        self.notes_pending = 0

    def get_notes_pending(self):
        return self.notes_pending

    def panic(self):
        if self.midi.is_port_open() == False:
            return

        log.info(f"Panic")
        for channel in range(16):
            self.midi.send_message([CONTROL_CHANGE, ALL_SOUND_OFF, 0])
            self.midi.send_message([CONTROL_CHANGE, RESET_ALL_CONTROLLERS, 0])
            time.sleep(0.05)

    def send_message(self, message):
        if self.midi.is_port_open() == False:
            return

        log.info(f"{self.port_name} - Note out: {message}")
        data_type = message[0]
        if data_type is NOTE_OFF:
            self.notes_pending -= 1
        if data_type is NOTE_ON:
            self.notes_pending += 1

        self.midi.send_message(message)

    def send_clock_message(self):
        if self.midi.is_port_open() == False:
            return

        self.midi.send_message([TIMING_CLOCK])

    def __destroy__(self):
        self.panic()
        del self.midi


class MidiInternalClock:
    """
    looks like a MidiInput object, but runs off a internal clock instead of a external midi clock
    can send clocks externally though
    """
    def __init__(self, midiout=None, bpm=60):
        self.bpm = bpm
        self.midiout = midiout
        self.clock_callback = None
        self.clock_data = None
        self.clock_counts = 0
        # 24 beats per quarter note, (60/60)/24 = 41.6 msec
        self.tick_time = (60.0/self.bpm)/24.0
        self.time_alarm = False # gets set if we run out of time between ticks

    def get_tick(self):
        return self.clock_counts

    def register_clock_callback(self, callback, data=None):
        self.clock_callback = callback
        self.clock_data = data

    def callback(self):
        while True:
            start = time.time()
            if self.midiout is not None:
                # we are also sending messages in the background, so lets hope we are synced
                self.midiout.send_clock_message() 

            self.clock_counts += 1           # number of clock msgs since inception
            self.clock_callback(self.clock_counts, self.clock_data)
            time_to_sleep = self.tick_time - (time.time() - start) # subtract off time we worked
            #log.info(f"Internal clock sleepy time: {time_to_sleep}")
            if time_to_sleep <= 0.0:
                self.time_alarm = True
            else:
                time.sleep(time_to_sleep)

    def run(self):
        if self.clock_callback is None:
            return
        log.info(f"Starting internal clock: {self.tick_time}")
        timerThread = threading.Thread(target=self.callback)
        timerThread.start()
        

class MidiNoteMessage:
    def __init__(self, message):
        self.data_type = message[0]
        if self.data_type is NOTE_OFF or self.data_type is NOTE_ON:
            self.velocity = message[2]
            self.note = message[1]
        else:
            raise Exception('Not a midi note message')

    def get_message(self):
        return [self.data_type, self.note, self.velocity]



class Effect:
    """
    Things common to midi effects
    """
    def __init__(self):
        self.name = 'MIDI Effect'
        self.control_map = {}

    def get_name(self):
        return self.name

    def control_to_selection(self, selections, control):
        """
        a cc value is mapped to a range of selections in a list
        """
        n = len(selections)
        s = 128/n
        t = int(control/s)
        if t > n - 1:
            t = n - 1

        return t

    def run(self):
        pass # override



class NoteManager:
    """
    A simple priority queue of note events
    These are added at clock tick priority and examined 
    if it is their time to be sent out
    """

    def __init__(self):
        self.note_events = queue.PriorityQueue()

    def run(self, tick, midiout):
        """
        See if any events are ready to play
        """
        if self.note_events.empty():
            return

        # no peek ;(
        event = self.note_events.get()

        if tick >= event[0]:
            log.info(f"Run: {tick}")
            midiout.send_message(event[1])
        else:
            self.note_events.put(event)

    def add(self, tick, message):
        """
        Add a message to the priority queue
        """
        self.note_events.put((tick,message))
        log.info(f"Add: {message}, {tick}")

    def empty(self):
        return self.note_events.empty()


class MidiManager:
    """
    Manages midi in, midi out and midi clock
    """

    def __init__(self):
       self.midiin = MidiInput()
       self.midiout = MidiOutput()
       self.clock_midiout = None # set to self.midiout if we want to send clock out this port. 
       self.clock_midiin = None # can be set to a midiin port to get external clock
       self.internal_clock = True # set to false with above if effect does not need a clock
       self.clock_callback = None
       self.clock_data = None
       self.internal_clock_bpm = 60
       self.set_midi_clock_internal()

    def get_midi_in_ports(self):
        try:
            names = self.midiin.get_port_names()
        except:
            return None
        return names

    def get_midi_out_ports(self):
        try:
            names = self.midiout.get_port_names()
        except:
            return None
        return names

    def set_midi_in_port(self, name):
        try:
            self.midiin.open_port(name)
        except:
            return False
        return True

    def set_midi_out_port(self, name):
        try:
            self.midiout.open_port(name)
        except:
            return False
        return True

    def set_midi_clock_internal(self, set=True):
        #if set:
        self.clock_source = MidiInternalClock(midiout=self.clock_midiout, bpm=self.internal_clock_bpm)
        self.internal_clock = True
        #else:
        #    self.clock_source = MidiInput(ignore_clock=False) # 'lmb'

        self.clock_source.register_clock_callback(callback=self.clock_callback, data=self.clock_data)   

        # wip a lot more logic here and there...


    def register_note_callback(self, callback):
        self.midiin.register_note_callback(callback, self.clock_source) # pass clock source so we know when notes arrive

    def register_clock_callback(self, callback, data=None):
        if self.clock_source is not None:
            self.clock_source.register_clock_callback(callback, data) 
        # rememeber in case we switch clock sources
        self.clock_callback = callback
        self.clock_data = data

    def register_control_callback(self, callback, data=None):
        self.midiin.register_control_callback(callback, data)
 

    def panic(self):
        self.midiout.panic()
