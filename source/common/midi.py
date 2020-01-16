"""
 Copyright (C) 2020 Brian R. Gunnison
 
 This file is part of MIDI project
 
 MIDI can not be copied and/or distributed without the express
 permission of Brian R. Gunnison
"""
import time
import threading
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
        self.midi_activity_callback = None

    def register_midi_activity_callback(self, callback):
        self.midi_activity_callback = callback

    def get_port_names(self):
        self.ports = self.midi.get_ports()
        if len(self.ports) == 0:
            raise Exception("No MIDI in ports found")
        return self.ports

    #def error_callback(self, func, data);

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
                break

        if port_index is None:
            raise Exception(f'Cannot find desired port named {name}')

        try:
            self.midi.open_port(port_index)
        except InvalidUseError:
            self.last_error = f'Cannot open MIDI port: {name}, in use'
            raise Exception(self.last_error)
        except InvalidPortError:
            self.last_error = f'Cannot open MIDI port: {name}, bad port number'
            raise Exception(self.last_error)
        except TypeError:
            self.last_error = f'Cannot open MIDI port: {name}, internal error'
            raise Exception(self.last_error)

        self.port_name = self.midi.get_port_name(port_index)
        log.info(f"Opened MIDI port: {self.port_name}")

        #self.midi.set_error_callback(self.error_callback)

    def close_port(self):
        self.midi.close_port()
        log.info(f"Closed MIDI port: {self.port_name}")
        self.port_name = None

    def __destroy__(self):
        self.close_port()
        del self.midi

gstart_debug_timer = 0.0

class MidiInput(MidiPort):
    def __init__(self, q_size_limit=1024, ignore_clock=True):
        super().__init__()
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
        global gstart_debug_timer
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
                gstart_debug_timer = time.time()
                
                log.info(f"{self.port_name} - Note In: {message}")
                self.note_callback(message, self.clock_midiin)
                if self.midi_activity_callback is not None:
                    self.midi_activity_callback()

        if self.control_callback is not None:
            if data_type is CONTROL_CHANGE:
                log.info(f"{self.port_name} - Control: {message}")
                self.control_callback(message[1], message[2])
                if self.midi_activity_callback is not None:
                    self.midi_activity_callback()

    def run(self):
        self.midi.set_callback(self.callback)


class MidiOutput(MidiPort):
    def __init__(self):
        super().__init__()
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
        time_passed = time.time() - gstart_debug_timer
        log.info('tp: %.03f' % time_passed)

        if self.midi_activity_callback is not None:
            self.midi_activity_callback()


    def send_clock_message(self):
        if self.midi.is_port_open() == False:
            return

        self.midi.send_message([TIMING_CLOCK])

    

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

    def close_midi_out_port(self):
        try:
            self.midiout.close_port()
        except:
            return False
        return True

    def close_midi_in_port(self):
        try:
            self.midiin.close_port()
        except:
            return False
        return True

    def change_clock_bpm(self, value):
        if self.internal_clock:
            self.clock_source.change_bpm(value)
            
    def get_clock_bpm(self):
        return self.clock_source.get_bpm()

    def set_midi_clock_internal(self, set=True):
        #if set:
        self.clock_source = MidiInternalClock(midiout=self.clock_midiout)
        self.internal_clock = True
        #else:
        #    self.clock_source = MidiInput(ignore_clock=False) # 'lmb'

        self.clock_source.register_clock_callback(callback=self.clock_callback, data=self.clock_data)   

        # wip a lot more logic here and there...

    def register_midiin_activity_callback(self, callback):
        self.midiin.register_midi_activity_callback(callback)

    def register_midiout_activity_callback(self, callback):
        self.midiout.register_midi_activity_callback(callback)


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


# wip create clock class for this and midiin
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
        self.tick = 0 
        # 24 beats per quarter note, (60/60)/24 = 41.6 msec
        self.tick_time = (60.0/self.bpm)/24.0
        self.time_alarm = False # gets set if we run out of time between ticks

    def change_bpm(self, bpm):
        if self.bpm == 0:
            return

        self.bpm = bpm
        self.tick_time = (60.0/self.bpm)/24.0
        log.info(f'internal bpm: {bpm}')

    def get_bpm(self):
        return self.bpm

    def get_tick(self):
        return self.tick

    def register_clock_callback(self, callback, data=None):
        self.clock_callback = callback
        self.clock_data = data

    def callback(self):
        while True:
            if self.clock_callback is None:
                return # exit thread

            start = time.time()
            if self.midiout is not None:
                # we are also sending messages in the background, so lets hope we are synced
                self.midiout.send_clock_message() 

            self.tick += 1           # number of clock msgs since inception
            self.clock_callback(self.tick, self.clock_data)
            time_to_sleep = self.tick_time - (time.time() - start) # subtract off time we worked
            #log.info(f'Internal clock sleepy time: {time_to_sleep}, tick: {self.clock_counts}')
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

    def stop(self):
        self.clock_callback = None

    def send_clock_out(self, midiout):
        self.midiout = midiout
        

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

