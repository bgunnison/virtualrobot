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

logging.basicConfig(level=logging.ERROR)
log = logging.getLogger(__name__)

BPM_MIN = 10
BPM_MAX = 300 # also in the kv slider file

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
        self.midiin_callback = None
        self.channel_filter = 0 # 0 accepts or sends all channels WIP

    def set_channel_filter(self, filter):
        if filter > 16:
            filter = 0

        self.channel_filter = filter

    def get_channel_filter(self):
        return self.channel_filter

    def register_midi_activity_callback(self, callback):
        self.midi_activity_callback = callback

    def get_port_names(self):
        
        n = self.midi.get_port_count()
        if n == 0:
             raise Exception("No MIDI ports found")

        self.ports = []
        for p in range(n):
            name = self.midi.get_port_name(p)
            #log.info(f'Actual port name: {name}')
            # in windows the ports are enumerated in the name i.e. lma 1, where the 1 changes on PC reboot
            # so strip off the number so we open the same port next power cycle
            s = name.split(' ')
            if s[-1].isdigit():
                s = s[:-1]
                name = ' '.join(s)

            self.ports.append(name)

        return self.ports

    #def error_callback(self, func, data);

    def remember_midin_callback(self, callback): 
        self.midiin_callback = callback

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

        self.port_name = port_name # self.midi.get_port_name(port_index)
        log.info(f"Opened MIDI port: {self.port_name}")
        if self.midiin_callback  is not None:
            self.midi.set_callback(self.midiin_callback)


        #self.midi.set_error_callback(self.error_callback) not necessary

    def close_port(self):
        if self.midi.is_port_open() == True:
            self.midi.close_port() # safely removes callback for midiin
            log.info(f"Closed MIDI port: {self.port_name}")
        self.port_name = None

    def __del__(self):
        self.close_port()
        del self.midi

gstart_debug_timer = 0.0

class MidiClockSource:
    """
    base class for a clock source either external or internal
    """
    def __init__(self):
        self.bpm = BPM_MIN 
        self.clock_callback = None
        self.tick = 0
        self.midiout = None

    def get_bpm(self):
        if self.bpm < BPM_MIN:
            log.error(f'BPM too low:  {self.bpm}')
            return BPM_MIN

        if self.bpm > BPM_MAX:
            log.error(f'BPM too high:  {self.bpm}')
            return BPM_MAX

        return self.bpm

    def change_bpm(self, bpm):
        pass # override

    def send_clock_out(self, midiout):
        self.midiout = midiout

    def register_clock_callback(self, callback, data=None):
        self.clock_callback = callback
        self.clock_data = data
        self.tick = 1
        self.clock_delta_time = 0.0

    def start_clock(self):
        pass # override
    
    def stop_clock(self):
        self.clock_callback = None
        self.clock_data = None
        #log.info('stopping clock')

    def get_tick(self):
        return self.tick

    def process_tick(self):
        if self.midiout is not None:
            self.midiout.send_clock_message() 

        self.tick += 1           # number of clock msgs since inception
        if self.clock_callback is not None:
            self.clock_callback(self.tick, self.clock_data)
        else:
            log.error('Clock callback is None')


class MidiInternalClock(MidiClockSource):
    """
    looks like a MidiInput object, but runs off a internal clock instead of a external midi clock
    can send clocks externally though
    """
    def __init__(self, settings, cc_controls=None, bpm=60):
        super().__init__()
        self.settings = settings
        self.min = self.settings.get('internal_clock_bpm_min', BPM_MIN)
        self.max = self.settings.get('internal_clock_bpm_max', BPM_MAX)
        self.bpm = self.settings.get('internal_clock_bpm', bpm)
        if self.bpm < self.min:
            self.bpm = self.min

        self.cc_controls = cc_controls
        # 24 beats per quarter note, (60/60)/24 = 41.6 msec
        self.tick_time = (60.0/self.bpm)/24.0
        self.time_alarm = False # gets set if we run out of time between ticks
        if self.cc_controls is not None:
            self.cc_controls.add(name='InternalClockBPMControlCC',
                                 cc_default=28, # must be unique to effect CCs
                                 control_callback=self.change_bpm,
                                 min=self.min,
                                 max=self.max)

    def change_bpm(self, bpm):
        if bpm < self.min:
            return

        if bpm > self.max:
            return

        self.bpm = bpm
        self.tick_time = (60.0/self.bpm)/24.0
        #log.info(f'internal bpm: {bpm}')
        self.settings.set('internal_clock_bpm', self.bpm)

    def callback(self):
        while True:
            if self.clock_callback is None:
                log.info('Exiting internal clock thread')
                return # exit thread

            start = time.perf_counter()

            self.process_tick()
            
            time_to_sleep = self.tick_time - (time.perf_counter() - start) # subtract off time we worked
           # log.info(f'Internal clock tick: {self.tick}')
            if time_to_sleep <= 0.0:
                self.time_alarm = True
                log.error('Internal clock work took too long')
                time.sleep(self.tick_time) # gotta sleep else we get stuck here
            else:
                time.sleep(time_to_sleep)

    def start_clock(self):
        if self.clock_callback is None:
            return
        log.info(f"Starting internal clock: {self.tick_time:.03f}")
        timerThread = threading.Thread(target=self.callback)
        timerThread.start()



class MidiInput(MidiPort, MidiClockSource):
    def __init__(self, q_size_limit=1024):
        MidiPort.__init__(self)
        MidiClockSource.__init__(self)
        self.midi = rtmidi.MidiIn(queue_size_limit=q_size_limit)
        
        self.note_callback = None
        self.clock = None   # clock source
        self.control_callback = None
        self.control_data = None
        # need to average the delta time if external clock comes in here so to display a non-jerky BPM
        self.ext_clock_update_period = 0.5 # update every half second for UI
        self.last_ext_clock_time = time.perf_counter()
        self.last_ext_tick_update = self.tick
        self.rave_order = 6
        self.rave_samples = []
        self.rave_sum = 0

    def register_note_callback(self, callback):
        self.note_callback = callback

    def set_clock_source(self, clock):
        self.clock = clock

    def register_control_callback(self, callback, data=None):
        self.control_callback = callback
        self.control_data = data

    def calc_ext_clock_bpm(self):
        """
        This runs every clock tick, so we are only interested in updated the UI approx.
        """
        now = time.perf_counter()
        tp = now - self.last_ext_clock_time
        if tp < self.ext_clock_update_period:
            return

        self.last_ext_clock_time = now
        ticks = self.tick - self.last_ext_tick_update
        self.last_ext_tick_update = self.tick

        # so now we know how many ticks passed in .5 seconds

        clock_delta_time = self.ext_clock_update_period/float(ticks)
        if len(self.rave_samples) == self.rave_order:
            self.rave_sum -= self.rave_samples.pop(0)

        self.rave_sum += clock_delta_time
        self.rave_samples.append(clock_delta_time)
        ave_delta_time = self.rave_sum/float(len(self.rave_samples))

        # to get bpm from an external clock we use the delta time
        # self.tick_time = (60.0/self.bpm)/24.0
        # since it is not too accurate we average it
        self.bpm = round(60/(24 * ave_delta_time))

        #log.info(f'bpm: {self.bpm}')



    def callback(self, msg_dt, data):
        global gstart_debug_timer
        message = msg_dt[0]
        data0 = message[0]
        data_type = message[0] & 0xF0 # now we accept all channels

        if self.clock_callback is not None:
            if data0 == TIMING_CLOCK: # F8
                #msg_dt[1] is supposed to be time between clocks, but inaccurate
                #log.info(f'external clock tick: {self.tick}')
                self.process_tick()

                # all this so we can display external clock rate on UI
                self.calc_ext_clock_bpm()
                return 

        if self.note_callback is not None:
           
            if data_type == NOTE_OFF or data_type == NOTE_ON:
                gstart_debug_timer = time.perf_counter()
                
                #log.info(f"{self.port_name} - Note In: {message}")
                self.note_callback(message, self.clock)
                if self.midi_activity_callback is not None:
                    self.midi_activity_callback()
                return

        if self.control_callback is not None:
            if data_type == CONTROL_CHANGE:
                #log.info(f"{self.port_name} - Control: {message}")
                self.control_callback(message[1], message[2], self.control_data)
                if self.midi_activity_callback is not None:
                    self.midi_activity_callback()

    def start_clock(self):
        super(MidiInput, self).start_clock()
        self.midi.ignore_types(timing = False) # don't ignore MIDI clock messages
        self.rave_samples = []
        self.rave_sum = 0
        log.info(f'Midiin set as clock source')


    def stop_clock(self):
        super(MidiInput, self).stop_clock()
        self.midi.ignore_types(timing = True)
        log.info(f'Midiin ignoring clock')

    def run(self):
        self.midi.set_callback(self.callback)
        self.remember_midin_callback(self.callback) # reregister if port is changed



class MidiOutput(MidiPort):
    def __init__(self):
        super().__init__()
        self.midi = rtmidi.MidiOut()
        self.notes_pending = 0

    def get_notes_pending(self):
        # not a reliable method to see if any stuck notes...
        return self.notes_pending

    def panic(self):
        if self.midi.is_port_open() == False:
            return

        self.notes_pending = 0
        log.info(f"Panic")
        for channel in range(16):
            data = CONTROL_CHANGE + channel
            try:
                self.midi.send_message([data, ALL_SOUND_OFF, 0])
            except:
                log.error('Cant panic is port open?')
                return

            #self.midi.send_message([data, RESET_ALL_CONTROLLERS, 0])
            time.sleep(0.05)

    def purge(self):
        self.notes_pending = 0

    def send_message(self, message):
        if self.midi.is_port_open() == False:
            return

        #log.info(f"{self.port_name} - Note out: {message}")
        data_type = message[0] & 0xF0 # all channels
        if data_type == NOTE_OFF:
            self.notes_pending -= 1
        if data_type == NOTE_ON:
            self.notes_pending += 1

        #log.info(f'notes pending: {self.notes_pending}')
        try:
            self.midi.send_message(message)
        except:
            log.error('Cant send midi message, port closed?')

        time_passed = time.perf_counter() - gstart_debug_timer
        #log.info(f'tp: {time_passed:.04f}')

        if self.midi_activity_callback is not None:
            self.midi_activity_callback()


    def send_clock_message(self):
        if self.midi.is_port_open() == False:
            return
        try:
            self.midi.send_message([TIMING_CLOCK])
        except:
            log.error('Cant send clock, port closed?') # devices can be powered off



class MidiManager():
    """
    Manages midi in, midi out and midi clock
    """

    def __init__(self, settings, use_clock=True):
        self.settings = settings
        self.midiin = MidiInput()
        self.midiout = MidiOutput()
        self.cc_controls = CCControls(settings, self.midiin)
        self.internal_clock = None
        self.clock_callback = None
        self.clock_data = None
        self.clock = None # clock object
        self.clock_source = None
        if use_clock:
            # clock stuff
            self.internal_clock = MidiInternalClock(self.settings, cc_controls=self.cc_controls)
            self.clock_source = self.settings.get('ClockSource', 'internal')
            self.set_clock_source(self.clock_source)


    def get_midi_in_ports(self):
        try:
            names = self.midiin.get_port_names()
        except:
            log.debug('No input ports')
            return None

        log.info(f'Input ports: {names}')
        return names

    def get_midi_out_ports(self):
        try:
            names = self.midiout.get_port_names()
        except:
            log.debug('No output ports')
            return None

        log.info(f'Input ports: {names}')
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

            
    def set_clock_source(self, clock_source):
        if clock_source == self.clock_source and self.clock is not None:
            return  # no change

        if self.clock is not None:
            self.clock.stop_clock() # gracefully stop clock at the source

        if clock_source == 'internal':
            self.clock = self.internal_clock

        if clock_source == 'external':
            self.clock = self.midiin

        self.clock.register_clock_callback(callback=self.clock_callback, data=self.clock_data)  
        self.clock.send_clock_out(self.midiout) # might make option...
        # pass clock so we know when notes arrive
        self.midiin.set_clock_source(self.clock)
        self.clock.start_clock()
        self.clock_source = clock_source
        self.settings.set('ClockSource', clock_source)


    def register_midiin_activity_callback(self, callback):
        self.midiin.register_midi_activity_callback(callback)

    def register_midiout_activity_callback(self, callback):
        self.midiout.register_midi_activity_callback(callback)

    def register_note_callback(self, callback):
        self.midiin.register_note_callback(callback) 
        # pass clock so we know when notes arrive
        self.midiin.set_clock_source(self.clock)

    def register_clock_callback(self, callback, data=None):
        """
        called from effect manager to register its clock callback
        """
        if self.clock is not None:
            self.clock.stop_clock()
            self.clock.register_clock_callback(callback, data) 
            self.clock.start_clock()

        # rememeber in case we switch clock sources
        self.clock_callback = callback
        self.clock_data = data


    def panic(self):
        self.midiout.panic()

    def destroy(self):
        """
        app exiting make sure all is stopped and closed
        """
        if self.internal_clock is not None:
            self.internal_clock.register_clock_callback(callback=None)
        self.midiin.close_port()
        self.midiout.close_port()


class CCControls:
    """
    contains the CC control mapping and functionality
    A singleton
    """
    def __init__(self, settings, midiin):
        self.settings = settings
        self.midiin = midiin
        self.cc_controls = {}    # a dict keyd by cc number, cannot have two controls with same cc
        self.learn_name = None    # set to cc name to remap during midi learn
        self.ui_learn_callback = None # callback to ui when learning

        # last
        self.midiin.register_control_callback(self.callback, None)
      

    def get_cc_str(self, name):
        for cc, info in self.cc_controls.items():
            if name == info.get('name'):
                return str(cc)
        return ''

    def add(self, name, cc_default,  control_callback, type='cont', min=0, max=127, ui_callback=None):
        """
        An effect adds its cc controls at init here
        The cc number must be unique
        """
        cc = self.settings.get(name, cc_default)

        if self.cc_controls.get(cc) is not None:
            log.error(f'CC {cc} already added')
            return


        self.cc_controls[cc] = {'name':name,    # accessed by name
                                'control_callback':control_callback, # midi callback
                                'type':type,    # continuous or a switch (0 = off, > 0 is on)
                                'min':min,        # map 0 - 127 to min/max
                                'max':max,
                                'ui_callback':ui_callback}  # call up to UI to change widgets

        log.info(f'Added CC {cc} as {name}')

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


    def get_cc(self, name):
        if name is not None:
            for cc, info in self.cc_controls.items():
                if info.get('name') == name:
                    return cc

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

    def dump(self):
        for cc, info in self.cc_controls.items():
            log.info(f"{cc} - {info['name']}")
            log.info(f"   {info['type']}, {info['min']}, {info['max']}")

    def remap(self, name, cc):
        """
        find the named cc info and change its cc number
        """
        # bug fix - learning an already mapped CC forgets the other cc
        old_info = self.cc_controls.get(cc)
        if old_info is not None:
            if old_info.get('name') == name:
                return True # already mapped to thsi cc
            return False # cannot map to a CC in use

        for oldcc, info in self.cc_controls.items():
            if name == info.get('name'):
                log.info(f'Remapping {name} cc: {oldcc} to {cc}')
                del self.cc_controls[oldcc] # del first in case same cc #
                self.cc_controls[cc] = info
                self.settings.set(name, cc)
                self.dump()
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

    def get_ui_callback(self, name):
        """
        get the ui callback named
        """
        for cc, info in self.cc_controls.items():
            if info.get('name') == name:
                cbi = info.get('ui_callback')
                if cbi is None:
                    log.error(f'get_ui_callback for {name} no callback')
                    return None

                return cbi[0]

        log.error(f'get_ui_callback for {name} does not exist')
        return None

        
    def learn(self, name, ui_callback=None, ui_data=None):
        """
        set midin callback to learn for this cc name
        """
        for cc, info in self.cc_controls.items():
            if name == info.get('name'):
                #log.info(f'Learning cc for {name}')
                self.midiin.register_control_callback(self.cc_learn_callback, ui_data)
                self.ui_learn_callback = ui_callback
                self.learn_name = name
                return True

        log.error(f'Cannot learn cc for {name} as it does not exist')
        return False

    def unlearn(self):
        """
        set midin callback back to control
        """
        self.ui_learn_callback = None
        self.learn_name = None
        self.midiin.register_control_callback(self.callback, None)
        log.info(f'unlearn')
                

    def cc_learn_callback(self, cc, control, data):
        """
        midi input calls this in learn mode to remap the incoming cc to the 
        registered "learn" control name. We also call back up to the UI with the new cc number
        """
        if self.learn_name is None:
            return

        if self.remap(self.learn_name, cc) == False:
            return

        if self.ui_learn_callback is not None:
            self.ui_learn_callback(self.learn_name, cc, data)

      

    def callback(self, cc, control, data):
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
            

class MidiMessage:
    """
    compose a midi message from its parts
    channels are 0 - 15
    """
    def __init__(self, midi_number, velocity=127, note_on=True, channel=0):
        if note_on:
            type = NOTE_ON
        else:
            type = NOTE_OFF

        self.message = [type & 0xF0 | channel, midi_number, velocity]

    def get_message(self):
        return self.message



class MidiNoteMessage:
    """
    decompose a midi message to its parts
    """
    def __init__(self, message):
        self.data_type = message[0] & 0xF0
        self.channel = message[0] & 0x0F
        if self.data_type == NOTE_OFF or self.data_type == NOTE_ON:
            self.velocity = message[2]
            self.note = message[1]
            self.type_channel = message[0]
        else:
            raise Exception('Not a midi note message')

    def get_message(self):
        return [self.type_channel, self.note, self.velocity]

    def is_note_on(self):
        if self.data_type == NOTE_ON:
            return True
        return False

    def is_note_off(self):
        if self.data_type == NOTE_OFF:
            return True
        return False

    def make_note_off(self):
        self.type_channel = NOTE_OFF + self.channel

    def make_note_on(self):
        self.type_channel = NOTE_ON + self.channel


NOTES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
MIN_OCTAVE = -1
MAX_OCTAVE = 9
OCTAVES = list(range(11))
NOTES_IN_OCTAVE = len(NOTES)

def midi_number_to_note(number):
    """
    convert midi note number to string i.e. "C2"
    """
    octave = number // NOTES_IN_OCTAVE
    note = NOTES[number % NOTES_IN_OCTAVE] + str(octave)
    return note

def note_to_midi_number(octave, note):
    """
    convert octave and string note to midi number
    octaves are -1, 0 - 9 midi notes 0 - 127 stops at G9
    o
    """
    try:
        ni = NOTES.index(note)
    except ValueError:
        log.error(f'Bad note {note}')
        return None

    octave += 1

    number = ni + (octave * 12)

    if number < 0 or number > 127:
        log.error('Bad midi note or octave')
        return None

    return number


