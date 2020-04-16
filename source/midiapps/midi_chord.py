"""
 Copyright (C) 2020 Brian R. Gunnison
 
 This file is part of MIDI CHORD project
 
 MIDI CHORD can not be copied and/or distributed without the express
 permission of Brian R. Gunnison
"""
import os
import sys
import logging


#sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

from common.midi import *
from common.upper_class_utils import Effect, NoteManager


def fatal_exit(msg):
    print(msg)
    exit(0)

            

class ChordInfo:
    """
    Info about chords
    """
    def __init__(self):
        # display names and intervals
        self.info = {  'Major':[4,7],
                        'Minor':[3,7],
                        'Dim':[3,6],
                        'Major 7th':[4,7,11],
                        'Minor 7th':[3,7,10],
                        'Dom 7th':[4,7,10],
                        'Sus2':[2,7],
                        'Sus4':[5,7],
                        'Aug':[4,8],
                        'Custom':[]
                        }

    def get_intervals(self, name):
        return self.info.get(name)

    def get_names(self):
        return list(self.info.keys())



class MidiChord:
    """
    We can iterate over the midi note produced by the chord type and width
    """
    def __init__(self, tonic=60, name='Major', width=3):
        self.name = name
        self.midi_notes = [] # a list of midi chord notes sans tonic
        width -= 1 # only generate the other chord notes
        chords = ChordInfo()
        intervals = chords.get_intervals(name)
        if intervals is None:
            log.critical(f'Unrecognized chord name {name}')
            raise Exception(f'Unrecognized chord name: {name}')

        iindex = 0
        for i in range(width):
            self.midi_notes.append(tonic + intervals[iindex])
            iindex += 1

            if len(self.midi_notes) == width:
                break

            if iindex == len(intervals):
                tonic += 12
                self.midi_notes.append(tonic)   # octave up
                iindex = 0

            if len(self.midi_notes) == width:
                break


    def notes(self):
        return self.midi_notes



class MidiChordEffect(Effect):
    """
    A MIDI effect to play a chord from one note. 
    The chord type can be changed as well as the width
    Other controls are strum to delay the other notes
    Future is to play the chords WRT to position ie. set the I, then other notes play II, III, IV etc. 
    """
    def __init__(self, settings, cc_controls=None):
        super().__init__(settings, cc_controls)
        self.note_manager = NoteManager()
        self.update = True # set if we need to update delays
        self.chord_names = ChordInfo().get_names()
        self.chord_index = self.settings.get('ChordEffectName', 0) # major chord
   # default a 3 note major chord 
        self.new_chord_index = self.chord_index
        self.chord_width = self.settings.get('ChordEffectWidth', 3) # triad
        self.new_chord_width = self.chord_width

        self.chord_strum = self.settings.get('ChordEffectStrum', 0) # 0 = no strum
        self.new_chord_strum = self.chord_strum

        # do last
        if self.cc_controls is not None:
            self.add_controls()



    def __str__(self):
        return f'Chord effect - Type: {self.chord_name}, Notes: {self.chord_width}'

    def panic(self):
        """
        cancels all future notes
        """
        self.note_manager.panic()

    def get_chord_name_label(self, index):
        if index >= len(self.chord_names):
            return 0
        return self.chord_names[index]


    def add_controls(self):
        """
        called at init to add cc controls map
        """
        # VI25 Alesis controller CC knobs start with 21
        self.cc_controls.add(name='ChordEffectNameControlCC',
                                 cc_default=22,
                                 control_callback=self.control_chord_name,
                                 min=0,
                                 max=len(self.chord_names) - 1)

        self.cc_controls.add(name='ChordEffectWidthControlCC',
                                 cc_default=23,
                                 control_callback=self.control_chord_width,
                                 min=1,
                                 max=8) # polyphony limit ?

        self.cc_controls.add(name='ChordEffectStrumControlCC',
                                 cc_default=24,
                                 control_callback=self.control_chord_strum,
                                 min=0,
                                 max=50) # in 100ths of seconds

    def control_chord_name(self, control):
        """
        All controls are mapped to the value range set in add_controls
        """
        # just in case...
        if control >= len(self.chord_names):
            log.error('Chord name control too big')
            return

        if self.chord_index == control:
            return

        self.panic() # halts notes in progress
        self.new_chord_index = control
        log.info(f"Chord: {self.chord_names[self.new_chord_index]}")

    def control_chord_width(self, control):
        """
        A All controls are mapped to the value range set in add_controls
        """
        if control == 0:
            return

        if control == self.chord_width:
            return

        # we do not need to stop anything

        self.new_chord_width = control
        log.info(f"Chord width: {self.new_chord_width}")

    def control_chord_strum(self, control):
        """
        A All controls are mapped to the value range set in add_controls
        """
        if control == self.chord_strum:
            return

        self.new_chord_strum = control
        log.info(f"Chord strum: {self.chord_strum}")


    def run(self, tick, midiout, message):
        """
        generate the added notes for the chord
        """
        if midiout.get_notes_pending() == 0:    # if we change in the middle of a chord playing we get stuck notes
            if self.chord_index != self.new_chord_index:
                self.chord_index = self.new_chord_index
            if self.chord_width != self.new_chord_width:
                self.chord_width = self.new_chord_width
            if self.chord_strum != self.new_chord_strum:
                self.chord_strum = self.new_chord_strum



        midiout.send_message(message)  # send original note event

        onote = MidiNoteMessage(message)
        try:
            chord = MidiChord(tonic=onote.note, name=self.chord_names[self.chord_index], width=self.chord_width)
        except:
            return

        strum_delay = self.chord_strum * 0.01
        note_count = 1
        for note in chord.notes():
            onote.note = note

            if onote.is_note_on() and strum_delay != 0:
                time.sleep(note_count * strum_delay)
                note_count += 1

            midiout.send_message(onote.get_message())

        
        

