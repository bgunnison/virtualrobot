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


def fatal_exit(msg):
    print(msg)
    exit(0)

            

class ChordInfo:
    """
    Info about chords
    """
    def __init__(self):
        self.info = {  'major':[4,7],
                        'minor':[3,7],
                        'diminished':[3,6],
                        'major seventh':[4,7,11],
                        'minor seventh':[3,7,10],
                        'dominant seventh':[4,7,10],
                        'suspended2':[2,7],
                        'suspended4':[5,7],
                        'augmented':[4,8]
                        }

    def get_intervals(self, name):
        return self.info.get(name)

    def get_names(self):
        return list(self.info.keys())



class Chord:
    """
    We can iterate over the midi note produced by the chord type and width
    """
    def __init__(self, tonic=60, name='major', width=3):
        self.midi_notes = [] # a list of midi chord notes sans tonic
        width -= 1 # only generate the other chord notes
        chords = ChordInfo()
        intervals = chords.get_intervals(name)
        if intervals is None:
            log.critical()
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



class ChordEffect(Effect):
    def __init__(self):
        self.chord_name = 'major'   # default a 3 note major chord 
        self.new_chord_name = self.chord_name
        self.chord_width = 3
        self.new_chord_width = self.chord_width
        """
        WIP see echo effect
        self.effect = ChordEffect()
        # VI25 Alesis controller CC knobs start with 21
        self.effect_controls = {    24:[self.effect.control_chord_name],
                                    25:[self.effect.control_chord_width]
                                }  # a dict keyed with CC numbers and a list of control functions mapped to that CC
        """


    def __str__(self):
        return f'Chord effect - Type: {self.chord_name}, Notes: {self.chord_width}'

    def control_chord_name(self, control):
        """
        All controls are 0 - 127 per CC
        """
        names = ChordInfo().get_names()
        t = self.control_to_selection(names, control)        
        self.new_chord_name = names[t]
        log.info(f"Chord: {self.new_chord_name}")

    def control_chord_width(self, control):
        """
        All controls are 0 - 127 per CC
        """
        # a polyphony issue, limit to 12
        width = control/10
        if width < 1:
            width = 1

        self.new_chord_width = int(width)
        log.info(f"Chord width: {self.new_chord_width}")

    def run(self, tick, midiout, message):
        """
        generate the added notes for the chord
        """
        if midiout.get_notes_pending() == 0:    # if we change in the middle of a chord playing we get stuck notes
            if self.chord_name != self.new_chord_name:
                self.chord_name = self.new_chord_name
            if self.chord_width != self.new_chord_width:
                self.chord_width = self.new_chord_width


        midiout.send_message(message)  # send original note event

        onote = MidiNoteMessage(message)
        chord = Chord(tonic=onote.note, name=self.chord_name, width=self.chord_width)

        for note in chord.notes():
            onote.note = note
            midiout.send_message(onote.get_message())

        
        

