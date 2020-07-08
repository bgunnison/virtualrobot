"""
 Copyright (C) 2020 Brian R. Gunnison
 
 This file is part of MIDI BEAT project
 
 MIDI BEAT can not be copied and/or distributed without the express
 permission of Brian R. Gunnison
"""
import os
import sys
import math
import logging
from collections import deque

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

from common.midi import MidiNoteMessage, MidiMessage, MidiConstants, note_to_midi_number, NOTES, MIN_OCTAVE, MAX_OCTAVE
from midiapps.midi_effect_manager import Effect

# uses a beat selector in UI to select a beat. 
# The UI then controls that beat
MAX_BEATS = 8 # simultaneous beat streams
MAX_LOOP_LENGTH = 32 # we euclidean fit the beats in this size loop max

class Bjorklund:
    def __init__(self, steps : int, pulses : int):
        if pulses > steps:
            raise ValueError    
        self.pattern = []
        if pulses == 0:
            self.pattern = [0] * steps
            return

        level = 0
        counts = []
        remainders = []
        divisor = steps - pulses

        remainders.append(pulses)
        while True:
            counts.append(divisor / remainders[level])
            remainders.append(divisor % remainders[level])
            divisor = remainders[level]
            level += 1
            if remainders[level] < 2:
                break
        counts.append(divisor)

        def build(level : int):
            if level == -1:
                self.pattern.append(0)
            elif level == -2:
                self.pattern.append(1)
            else:
                # recursion
                for i in range(0, int(counts[level])):
                    build(level - 1)
                if remainders[level] != 0:
                    build(level - 2)
        build(level)
        i = self.pattern.index(1)
        self.pattern = self.pattern[i:] + self.pattern[0:i]

    def get_pattern(self):
        return self.pattern


class Beat:
    """
    A euclidean beat manager
    The algorithm fits beats evenly spaced in the loop size. 
    Uses the 
    """
    def __init__(self, parms, index=0):
        self.index = index # which beat are we for logging
        self.parms = parms # dict of parms

        # we update note info in run loop to keep things synchronous
        self.update_notes = True
        try:
            self.make_notes()
        except:
            raise ValueError

        self.update = True
        try:
            self.calc_beats()
        except:
            raise ValueError

        self.mute = False
        self.check_mute()


    def make_notes(self):
        try:
            midi_note = note_to_midi_number(self.parms['Octave'], self.parms['Note'])
        except:
            raise ValueError

        self.note_on_message = MidiMessage(midi_note, velocity=self.parms['Loud']).get_message() # used to do note on
        self.note_off_message = MidiMessage(midi_note, velocity=self.parms['Loud'], note_on=False).get_message() # used to do note off
        self.update_notes = False

    def calc_beats(self, new_truths=True):
        loop = self.parms['Loop']
        beats = self.parms['Beats']
        bars = self.parms['Bars']
        if loop < beats:
            log.error('Loop < beats')
            self.update = False
            return

        if new_truths:
            try:
                b = Bjorklund(loop, beats)
                self.truths = b.get_pattern() # returns [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0]
            except:
                log.error('Beats > loop')
                raise ValueError

        if self.parms['Rotate'] != 0:
            dt = deque(self.truths) 
            dt.rotate(self.parms['Rotate']) 
            self.truths  = list(dt) 

        # every 4 * 24 pulses defines a bar, the loop fits in bars
        self.beat_ticks = round((bars * 4 * 24)/loop) - 1
        self.tick_count = 0 # we count ticks and when equal to above we examine our truths
        self.truth_index = 0

        log.info(f'Beat: {self.index}, Truths: {self.truths}')
        self.update = False

    def set(self, name, value):
        if self.parms.get(name) is None:
            log.error(f'Beat parm name {name} does not exist')
            return

        self.parms[name] = value
        
        if name == 'Note' or name == 'Octave' or name == 'Loud':
            self.update_notes = True
            return

        self.update = True

        self.check_mute()

    def check_mute(self):
        if self.parms['Beats'] == 0 or self.parms['Loud'] == 0:
            self.mute = True
        else:
            self.mute = False

    def get(self, name):
        if self.parms.get(name) is None:
            log.error(f'Beat parm name {name} does not exist')
            return None

        return self.parms[name]

    def purge(self, midiout):
        if midiout is None:
            return
     
        midiout.send_message(self.note_off_message)


    def run(self, tick):
        """
        called at clock rate to update and return a note message if any
        """
        #log.info(f'Run: {self.index}, tick: {tick}')
        if self.mute:
            return (self.note_off_message,) # must be iterable

        if self.update_notes:
            try:
                self.make_notes()
            except:
                log.error('Error making notes')
                return (None,None) 

        if self.update:
            try:
                self.calc_beats()
            except:
                return (None, None)

        msg_off = None
        msg_on = None

        self.tick_count += 1
        if self.tick_count == self.beat_ticks:
            self.tick_count = 0

            if self.truths[self.truth_index]:
                # send a beat
                # we turn off the last note
                msg_off = self.note_off_message
                msg_on = self.note_on_message

            self.truth_index += 1
            if self.truth_index == len(self.truths):
                self.truth_index = 0

        return (msg_off, msg_on) 


class BeatManager:
    """
    same interface as NoteManager, but plays looped beats in time
    """
    def __init__(self):
        self.mute = True
        self.beats = []
        self.midiout = None

    def run(self, tick, midiout):
        """
        See if any events are ready to play
        called at clock rate
        async Controls are modifying the beat parameters
        """
        self.midiout = midiout
        if self.mute == True:
            return

        #log.info(f't: {tick}')
        for beat in self.beats:
            messages = beat.run(tick)
            for message in messages:
                if message is not None:
                    midiout.send_message(message)
        

    def add(self, beat):
        """
        Add a beat to the list
        """
        self.beats.append(beat)

    def remove(self, beat_index):
        pass

    def enable(self):
        self.mute = False

    def disable(self):
        self.mute = True

    def purge_beats(self, midiout):
        for beat in self.beats:
            beat.purge(midiout)

    def purge(self, midiout):
        self.purge_beats(midiout)
        
    def panic(self):
        self.purge_beats(self.midiout)

    def is_empty(self):
        return True




class MidiBeatEffect(Effect):
    def __init__(self, settings, cc_controls=None):
        super().__init__(settings, cc_controls)
        self.name = 'Beat'
        self.note_manager = BeatManager() # called every tick to play scheduled notes
        # we have N beats going on all at once. 
        self.update_beat_index = self.settings.get('BeatEffectBeatSelect', 1) # set via UI to beat index that can be updated 1 - 8
        if self.update_beat_index == 0:
            log.error('BeatEffectBeatSelect was 0')
            self.settings.set('BeatEffectBeatSelect', 1)
        else:
            self.update_beat_index -= 1 # used as index

        self.control_names = []

        for b in range(MAX_BEATS):
            bars = self.settings.get(f'BeatEffectBars{b}', 4)
            loop = self.settings.get(f'BeatEffectLoop{b}', 16)
            beats = self.settings.get(f'BeatEffectBeats{b}', 4)
            if beats > loop:
                beats = loop
                self.settings.set(f'BeatEffectNumberBeats{b}', beats)

            octave = self.settings.get(f'BeatEffectOctave{b}', 4) # the octave and note are combined to make the midi note played per stream
            ni = self.settings.get(f'BeatEffectNote{b}', 0) 
            if ni >= len(NOTES):
                log.error('Note out of range in settings')
                self.settings.set(f'BeatEffectNote{b}', 0) 
                ni = 0

            note = NOTES[ni]
            loud = self.settings.get(f'BeatEffectLoud{b}', 127) # note velocity
            rotate = self.settings.get(f'BeatEffectRotate{b}', 0) # we shift the beats by this

            # name the parms so we can get and set by name
            parms = {'Octave':  octave,
                     'Note':    note,
                     'Loud':    loud, 
                     'Bars':    bars, 
                     'Loop':    loop, 
                     'Beats':   beats,
                     'Rotate':  rotate}
            try:
                beat = Beat(parms, b)
            except:
                log.error('Creating beat')
                continue

            self.note_manager.add(beat)

        if self.cc_controls is not None:
            self.add_controls()

    def __str__(self):
        return 'Beat effect'

    def enable(self):
        self.note_manager.enable()

    def disable(self):
        self.note_manager.disable()

    def panic(self):
        """
        All active notes are turned off
        """
        self.note_manager.panic()

    def purge(self, midiout):
        """
        override Effect as a mute
        called when effect disabled (or Mute button off)
        """
        self.note_manager.purge(midiout)

    def add_controls(self):
        """
        called at init to add cc controls map
        """
        # VI25 Alesis controller CC knobs start with 21
        # cc defaults must be unique

        # selects which beat is being modified
        # limitation is CC controls only operate on selected beat. 
        def next_cc():
            cc = 20
            while True:
                yield cc
                cc += 1

        ccs = next_cc()

        self.cc_controls.add(name='BeatEffectBeatSelectControlCC',
                                 cc_default=next(ccs),
                                 control_callback=self.control_beat_select,
                                 min=1,
                                 max=MAX_BEATS)

        # these control the beat selected above
        self.cc_controls.add(name='BeatEffectOctaveControlCC',
                                 cc_default=next(ccs),
                                 control_callback=self.control_octave,
                                 min=-1,
                                 max=9)

        self.control_names.append('Octave') # remember the names so selecting a beat can update its controls

        self.cc_controls.add(name='BeatEffectNoteControlCC',
                                 cc_default=next(ccs),
                                 control_callback=self.control_note,
                                 min=0,
                                 max=len(NOTES) - 1)

        self.control_names.append('Note') # remember the names so selecting a beat can update its controls

        self.cc_controls.add(name='BeatEffectLoudControlCC',
                                 cc_default=next(ccs),
                                 control_callback=self.control_loud,
                                 min=0,
                                 max=127)

        self.control_names.append('Loud') # remember the names so selecting a beat can update its controls

        self.cc_controls.add(name='BeatEffectBarsControlCC',
                                 cc_default=next(ccs),
                                 control_callback=self.control_bars,
                                 min=1,
                                 max=MAX_LOOP_LENGTH)

        self.control_names.append('Bars') # remember the names so selecting a beat can update its controls

        self.cc_controls.add(name='BeatEffectLoopControlCC',
                                 cc_default=next(ccs),
                                 control_callback=self.control_loop,
                                 min=1,
                                 max=MAX_LOOP_LENGTH)

        self.control_names.append('Loop') # remember the names so selecting a beat can update its controls


        self.cc_controls.add(name='BeatEffectBeatsControlCC',
                                 cc_default=next(ccs),
                                 control_callback=self.control_beats,
                                 min=0, # 0 disables beat stream
                                 max=MAX_LOOP_LENGTH)

        self.control_names.append('Beats') # remember the names so selecting a beat can update its controls

        self.cc_controls.add(name='BeatEffectRotateControlCC',
                                 cc_default=next(ccs),
                                 control_callback=self.control_rotate,
                                 min=0, 
                                 max=MAX_LOOP_LENGTH)

        self.control_names.append('Rotate') # remember the names so selecting a beat can update its controls


    def control_beat_select(self, control):
        if control >= MAX_BEATS + 1:
            log.error('control_beat_select control too big')
            return

        if control < 1:
            log.error('control_beat_select control too small')
            return

        self.update_beat_index = control - 1

        # get the beat params and update the sliders 
        # the slider ui callbacks are in the cc_controls
        for name in self.control_names:
            value = self.note_manager.beats[self.update_beat_index].get(name)
            if value is None:
                continue

            ui_name = 'BeatEffect' + name + 'ControlCC'

            ui_callback = self.cc_controls.get_ui_callback(ui_name)
            if ui_callback is None:
                continue

            if name == 'Note':
                value = NOTES.index(value)

            ui_callback(value, ui_name)

        
        self.settings.set('BeatEffectBeatSelect', control)
        log.info(f"control_beat_select: {control}")


    def control_octave(self, control):
        if control < MIN_OCTAVE or control > MAX_OCTAVE:
            log.error('control_octave control out of range')
            return

        self.note_manager.beats[self.update_beat_index].set('Octave', control)
        
        self.settings.set(f'BeatEffectOctave{self.update_beat_index}', control)
        log.info(f'control_beat_octave {self.update_beat_index}: {control}')


    def get_note_label(self, note_index):
        if note_index >= len(NOTES):
            return 'Unknown'

        return NOTES[note_index]


    def control_note(self, control):
        if control >= len(NOTES):
            log.error('control_beat_note control too big')
            return

        note = NOTES[control]

        self.note_manager.beats[self.update_beat_index].set('Note', note) # beat uses the letter note
        
        self.settings.set(f'BeatEffectNote{self.update_beat_index}', control) # we store the index
        log.info(f'control_beat_note {self.update_beat_index}: {note}')

    def control_loud(self, control):
        if control > 127:
            log.error('control_loud control too big')
            return

        self.note_manager.beats[self.update_beat_index].set('Loud', control)
        
        self.settings.set(f'BeatEffectLoud{self.update_beat_index}', control)
        log.info(f'control_loud {self.update_beat_index}: {control}')

    def control_bars(self, control):
        if control >= MAX_LOOP_LENGTH:
            log.error('control_bars control too big')
            return

        self.note_manager.beats[self.update_beat_index].set('Bars', control)
        
        self.settings.set(f'BeatEffectBars{self.update_beat_index}', control)
        log.info(f"control_bars {self.update_beat_index}: {control}")

    def control_loop(self, control):
        if control >= MAX_LOOP_LENGTH:
            log.error('control_loop control too big')
            return

        self.note_manager.beats[self.update_beat_index].set('Loop', control)
        
        self.settings.set(f'BeatEffectLoop{self.update_beat_index}', control)
        log.info(f"control_loop {self.update_beat_index}: {control}")


    def control_beats(self, control):
        if control >= MAX_LOOP_LENGTH:
            log.error('control_number_beats control too big')
            return

        self.note_manager.beats[self.update_beat_index].set('Beats', control)
        
        self.settings.set(f'BeatEffectBeats{self.update_beat_index}', control)
        log.info(f"control_beats {self.update_beat_index}: {control}")


    def control_rotate(self, control):
        if control >= MAX_LOOP_LENGTH:
            log.error('control_rotate control too big')
            return

        self.note_manager.beats[self.update_beat_index].set('Rotate', control)
        
        self.settings.set(f'BeatEffectRotate{self.update_beat_index}', control)
        log.info(f"control_rotate {self.update_beat_index}: {control}")


    def get_settings_xobject(self):
        """
        returns current object active in UI
        """
        return self.update_beat_index

    def run(self, tick, midiout, message):
        """
        note events are not used
        """
        midiout.send_message(message)  # send original note event

