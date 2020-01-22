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

class MidiConstants:
    """
    exported outside this file as well as here
    """
    def __init__(self):
        self.CC_MAX = 127


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

    def __del__(self):
        self.close_port()
        del self.midi

gstart_debug_timer = 0.0

class MidiInput(MidiPort):
    def __init__(self, q_size_limit=1024):
        super().__init__()
        self.midi = rtmidi.MidiIn(queue_size_limit=q_size_limit)

        self.note_callback = None

        self.clock_callback = None
        self.clock_midiin = None
        self.clock_delta_time = 0.0   # the time between clock msgs
        self.tick = 0

        self.control_callback = None
        self.control_data = None

    def register_clock_callback(self, callback, data=None):
        self.clock_callback = callback
        self.clock_data = data
        self.midi.ignore_types(timing = False) # don't ignore MIDI clock messages

    def stop_clock(self):
        self.clock_callback = None
        self.clock_data = None
        self.midi.ignore_types(timing = True) # ignore MIDI clock messages

    def register_note_callback(self, callback, clock_midiin):
        self.note_callback = callback
        self.clock_midiin = clock_midiin


    def register_control_callback(self, callback, data=None):
        self.control_callback = callback
        self.control_data = data

    def get_tick(self):
        return self.tick

    def callback(self, msg_dt, data):
        global gstart_debug_timer
        message = msg_dt[0]
        data_type = message[0]

        if self.clock_callback is not None:
            if data_type == TIMING_CLOCK:
                self.clock_delta_time = msg_dt[1]   # the time between clock msgs
                self.tick += 1           # number of clock msgs since inception
                self.clock_callback(self.tick, self.clock_data)
                return 

        if self.note_callback is not None:
            if data_type is NOTE_OFF or data_type is NOTE_ON:
                gstart_debug_timer = time.time()
                
                log.info(f"{self.port_name} - Note In: {message}")
                self.note_callback(message, self.clock_midiin)
                if self.midi_activity_callback is not None:
                    self.midi_activity_callback()
                return

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


class CCControls:
    """
    contains the CC control mapping and functionality
    A singleton
    """
    def __init__(self, settings):
        self.settings = settings
        self.cc_controls = {}    # a dict keyd by cc number

    def get_cc_str(self, name):
        for cc, info in self.cc_controls.items():
            if name == info.get('name'):
                return str(cc)
        return ''

    def add(self, name, cc_default,  control_callback, type='cont', min=0, max=127, ui_callback=None):
        cc = self.settings.get(name, cc_default)

        if self.cc_controls.get(cc) is not None:
            del self.cc_controls[cc]

        self.cc_controls[cc] = {'name':name,    # accessed by name
                                'control_callback':control_callback, # midi callback
                                'type':type,    # continuous or a switch (0 = off, > 0 is on)
                                'min':min,        # map 0 - 127 to min/max
                                'max':max,
                                'ui_callback':ui_callback}  # call up to UI to change widgets

    def get_max(self, name):
        for cc, info in self.cc_controls.items():
            if info.get('name') == name:
                return info.get('max')

        return 0

    def get_min(self, name):
        for cc, info in self.cc_controls.items():
            if info.get('name') == name:
                return info.get('min')

        return 0


    def delete(self, cc=None, name=None):
        if cc is not None:
            if self.cc_controls.get(cc) is not None:
                del self.cc_controls[cc]
                return

        if name is not None:
            for cc, info in self.cc_controls.items():
                if info.get(name) == name:
                    del self.cc_controls[cc]

    def remap(self, name, cc):
        """
        find the named cc info and change its cc number
        """
        for oldcc, info in self.cc_controls.items():
            if name == info.get('name'):
                self.cc_controls[cc] = info
                del self.cc_controls[oldcc]
                self.settings.set(name, cc)
                return True

        return False

    def register_ui_callback(self, name, callback, data=None):
        """
        adds a callback to the UI to change widgets during a cc
        """
        for cc, info in self.cc_controls.items():
            if info.get('name') == name:
                info['ui_callback'] = (callback, data)
                return True

        log.error(f'register_ui_control_callback for {name} - must add cc first')
        return False

    def callback(self, cc, control):
        """
        A cc button switches effects or
        An effect has controllable parms via CC knobs
        The app maps the CC to the parm(s). This callback has the CC number and control  (0 - 127)
        We use the CC to get the effect parm function and call it.
        """
        info = self.cc_controls.get(cc)
        if info is None:
            return

        control_callback = info.get('control_callback')
        if control_callback is None:
            log.error(f'CC map {cc} control callback is none')
            return

        if info['type'] == 'switch':
            if control == 0:
                value = False
            else:
                value = True
        else:
            range = info['max'] - info['min']
            value = int(info['min'] + (range * (control/127.0)))

        control_callback(value)

        ui_callback = info.get('ui_callback')

        if ui_callback is not None:
            ui_callback[0](value, ui_callback[1])


class MidiManager():
    """
    Manages midi in, midi out and midi clock
    """

    def __init__(self, settings):
        self.settings = settings
        self.cc_controls = CCControls(settings)
        self.midiin = MidiInput()
        self.midiout = MidiOutput()
        self.clock_midiout = None # set to self.midiout if we want to send clock out this port. 
        self.clock_midiin = None # can be set to a midiin port to get external clock
        self.internal_clock = False # set to false so the call below will make it internal
        self.clock_callback = None
        self.clock_data = None
        self.clock_source = None
        self.set_clock_source(internal=True)

        # last
        self.midiin.register_control_callback(self.cc_controls.callback, None)
      

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

            
    def set_clock_source(self, internal=True):
        if internal == self.internal_clock:
            return  # no change

        if self.clock_source is not None:
            self.clock_source.stop_clock() # gracefully stop clock at the source

        if internal:
            self.clock_source = MidiInternalClock(self.settings, midiout=self.clock_midiout, cc_controls=self.cc_controls)
            self.internal_clock = True
        else:
            self.internal_clock = False
            self.clock_source = self.midiin

        self.clock_source.register_clock_callback(callback=self.clock_callback, data=self.clock_data)   
        # wip a lot more logic here and there...

    def register_midiin_activity_callback(self, callback):
        self.midiin.register_midi_activity_callback(callback)

    def register_midiout_activity_callback(self, callback):
        self.midiout.register_midi_activity_callback(callback)

    def register_note_callback(self, callback):
        self.midiin.register_note_callback(callback, self.clock_source) # pass clock source so we know when notes arrive

    def register_clock_callback(self, callback, data=None):
        """
        called from effect manager to register its clock callback
        """
        if self.clock_source is not None:
            self.clock_source.register_clock_callback(callback, data) 
        # rememeber in case we switch clock sources
        self.clock_callback = callback
        self.clock_data = data


    def panic(self):
        self.midiout.panic()


# wip create clock class for this and midiin
class MidiInternalClock():
    """
    looks like a MidiInput object, but runs off a internal clock instead of a external midi clock
    can send clocks externally though
    """
    def __init__(self, settings, midiout=None, cc_controls=None, bpm=60):
        self.settings = settings
        self.min = self.settings.get('internal_clock_bpm_min', 10)
        self.max = self.settings.get('internal_clock_bpm_max', 240)
        self.bpm = self.settings.get('internal_clock_bpm', bpm)
        self.cc_controls = cc_controls
        self.midiout = midiout # send clock out if  exists
        self.clock_callback = None
        self.clock_data = None
        self.tick = 0 
        # 24 beats per quarter note, (60/60)/24 = 41.6 msec
        self.tick_time = (60.0/self.bpm)/24.0
        self.time_alarm = False # gets set if we run out of time between ticks
        if self.cc_controls is not None:
            self.cc_controls.add(name='InternalClockBPMControlCC',
                                 cc_default=29,
                                 control_callback=self.change_bpm,
                                 min=self.min,
                                 max=self.max)

    def stop_clock(self):
        """
        just stop
        """
        self.clock_callback = None
        self.clock_data = None

    def change_bpm(self, bpm):
        if bpm < self.min:
            return

        if bpm > self.max:
            return

        self.bpm = bpm
        self.tick_time = (60.0/self.bpm)/24.0
        log.info(f'internal bpm: {bpm}')
        self.settings.set('internal_clock_bpm', self.bpm)

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

