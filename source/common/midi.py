"""
stolen from isobar
"""
import time
import threading


try:
    import rtmidi
except:
    print("rtmidi not found, no MIDI support available.")
    exit(0)

from rtmidi.midiconstants import *

import logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

class MidiIn:
    def __init__(self, target = None, q_size_limit=1024, ignore_clock=True):
        self.midi = rtmidi.MidiIn(queue_size_limit=q_size_limit)

        if ignore_clock == False:
            self.midi.ignore_types(timing = False) #don't ignore MIDI clock messages

        if target is None:
            raise Exception("Must specify midi input port name")

        ports = self.midi.get_ports()
        if len(ports) == 0:
            raise Exception("No MIDI ports found")

        port_index = None
        for index, name in enumerate(ports):
            log.info(f"MIDI in port: {name}")
            if target in name:
                log.info(f"Found desired MIDI in port: {name}")
                port_index = index

        if port_index is None:
            raise Exception(f'Cannot find desired port named {target}')

        try:
            self.midi.open_port(port_index)
        except:
            raise Exception(f'Cannot open port {name}')

        self.port_name = self.midi.get_port_name(port_index)
        log.info(f"Opened MIDI input: {self.port_name}")

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


class MidiInternalClock:
    """
    looks like a midiin object, but runs off a internal clock instead of a external midi clock
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
        

class MidiOut:
    def __init__(self, target = None):
        self.midi = rtmidi.MidiOut()

        ports = self.midi.get_ports()
        if len(ports) == 0:
            raise Exception("No MIDI output ports found")

        port_index = None
        for index, name in enumerate(ports):
            log.info(f"MIDI output: {name}")
            if target in name:
                log.info(f"Found desired MIDI output: {name}")
                port_index = index
                break

        try:
            self.midi.open_port(port_index)
        except:
            raise Exception('Could not open desired midi output port')

        self.port_name = self.midi.get_port_name(port_index)
        log.info(f"Opened MIDI output: {self.port_name}")

        self.notes_pending = 0

    def get_notes_pending(self):
        return self.notes_pending

    def panic(self):
        log.info(f"Panic")
        for channel in range(16):
            self.midi.send_message([CONTROL_CHANGE, ALL_SOUND_OFF, 0])
            self.midi.send_message([CONTROL_CHANGE, RESET_ALL_CONTROLLERS, 0])
            time.sleep(0.05)

    def send_message(self, message):
        log.info(f"{self.port_name} - Note out: {message}")
        data_type = message[0]
        if data_type is NOTE_OFF:
            self.notes_pending -= 1
        if data_type is NOTE_ON:
            self.notes_pending += 1

        self.midi.send_message(message)

    def send_clock_message(self):
        self.midi.send_message([TIMING_CLOCK])

    def __destroy__(self):
        self.panic()
        del self.midi


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