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


sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

from common.midi import MidiNoteMessage, MidiMessage, MidiConstants
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
    def __init__(self, index=0, note=60, loop=16, beats=4):
        self.velocity = 127
        self.index = index
        self.note = note
        self.loop = loop
        self.beats = beats
        self.update = True
        self.last_message = None
        try:
            self.calc_beats()
        except:
            raise ValueError

    def calc_beats(self, new_truths=True):
        if new_truths:
            try:
                b = Bjorklund(self.loop, self.beats)
                self.truths = b.get_pattern() # returns [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0]
            except:
                log.error('Beats > loop')
                raise ValueError

        # every 4 * 24 pulses defines a bar, the loop fits in a bar
        beat_ticks = (4 * 24)/self.loop
        self.events = [] # a list of beat to beat in ticks
        tick = 0
        for truth in self.truths:
            if truth:
                self.events.append(tick)
            tick += beat_ticks
        
        log.info(f'Beat: {self.index}, Truths: {self.truths}, events: {self.events}')
        self.event_index = 0
        self.update = False

    def set_loop(self, loop):
        if loop < self.beats:
            log.error('loop < beats')
            return

        self.loop = loop
        self.update = True

    def set_beats(self, beats):
        if self.loop < beats:
            log.error('beats > loop')
            return

        self.beats = beats
        self.update = True

    def set_note(self, note):
        self.note = note

    def rotate(self, rotation):
        """
        rotates truths to the right
        """
        pass

    def run(self, tick):
        """
        called at clock rate to update and return a note message if any
        """
        #log.info(f'Run: {self.index}, tick: {tick}')
        if self.update:
            try:
                self.calc_beats()
            except:
                return (None, None)

        if self.event_index == 0:
            self.loop_start_tick = tick

        tp = tick - self.loop_start_tick
        if tp >= round(self.events[self.event_index]):
            self.event_index += 1
            if self.event_index == len(self.events):
                self.event_index = 0

            message = MidiMessage(self.note, self.velocity).get_message()
            self.last_message = message
            off = MidiNoteMessage(message)
            off.make_note_off()
            return (off.get_message(), message)

        return (None, None) # no note ready


class BeatManager:
    """
    same interface as NoteManager, but plays looped beats in time
    """
    def __init__(self):
        self.beats = []

    def run(self, tick, midiout):
        """
        See if any events are ready to play
        called at clock rate
        async Controls are modifying the beat parameters
        """
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

    def purge(self):
        pass

    def panic(self):
       pass

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


        for b in range(MAX_BEATS):
            try:
                beat = Beat( b, self.settings.get(f'BeatEffectBeatNote{b}', 60+b),
                                self.settings.get(f'BeatEffectLoopLength{b}', 16),
                                self.settings.get(f'BeatEffectNumberBeats{b}', 4))
            except:
                log.error('Creating beat')
                continue

            self.note_manager.add(beat)


        if self.cc_controls is not None:
            self.add_controls()

    def __str__(self):
        return 'Beat effect'

    def panic(self):
        """
        All active notes are turned off
        """
        pass

   
    def add_controls(self):
        """
        called at init to add cc controls map
        """
        # VI25 Alesis controller CC knobs start with 21
        # cc defaults must be unique

        # selects which beat is being modified
        # limitation is CC controls only operate on selected beat. 
        self.cc_controls.add(name='BeatEffectBeatSelectControlCC',
                                 cc_default=22,
                                 control_callback=self.control_beat_select,
                                 min=1,
                                 max=MAX_BEATS)

        # these control the beat selected above
        self.cc_controls.add(name='BeatEffectBeatNoteControlCC',
                                 cc_default=23,
                                 control_callback=self.control_beat_note,
                                 min=0,
                                 max=MidiConstants().CC_MAX)

        self.cc_controls.add(name='BeatEffectLoopLengthControlCC',
                                 cc_default=24,
                                 control_callback=self.control_loop_length,
                                 min=1,
                                 max=MAX_LOOP_LENGTH)

        self.cc_controls.add(name='BeatEffectNumberBeatsControlCC',
                                 cc_default=25,
                                 control_callback=self.control_number_beats,
                                 min=0, # 0 disables beat stream
                                 max=MAX_LOOP_LENGTH)



    def control_beat_select(self, control):
        if control >= MAX_BEATS + 1:
            log.error('control_beat_select control too big')
            return

        if control < 1:
            log.error('control_beat_select control too small')
            return

        self.update_beat_index = control - 1
        
        self.settings.set('BeatEffectBeatSelect', control)
        log.info(f"control_beat_select: {control}")

    def control_beat_note(self, control):
        if control >= MidiConstants().CC_MAX:
            log.error('control_beat_note control too big')
            return

        self.note_manager.beats[self.update_beat_index].set_note(control)
        
        self.settings.set(f'BeatEffectBeatNote{self.update_beat_index}', control)
        log.info(f'control_beat_note {self.update_beat_index}: {control}')


    def control_loop_length(self, control):
        if control >= MAX_LOOP_LENGTH:
            log.error('control_loop_length control too big')
            return

        self.note_manager.beats[self.update_beat_index].set_loop(control)
        
        self.settings.set(f'BeatEffectBeatLoop{self.update_beat_index}', control)
        log.info(f"control_loop_length {self.update_beat_index}: {control}")


    def control_number_beats(self, control):
        if control >= MAX_LOOP_LENGTH:
            log.error('control_number_beats control too big')
            return

        self.note_manager.beats[self.update_beat_index].set_beats(control)
        
        self.settings.set(f'BeatEffectNumberBeats{self.update_beat_index}', control)
        log.info(f"control_number_beats {self.update_beat_index}: {control}")

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

