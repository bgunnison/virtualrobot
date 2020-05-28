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
logging.basicConfig(level=logging.ERROR)
log = logging.getLogger(__name__)

from common.midi import *
from common.upper_class_utils import NoteManager
from midiapps.midi_effect_manager import Effect
from common.midi import MidiNoteMessage, MidiConstants


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
                        #'Custom':[]
                        }

    def get_intervals(self, name):
        return self.info.get(name)

    def get_names(self):
        return list(self.info.keys())
"""
 inversions
0   t   4               7

        third at bass
1   t   t-12 + 4        t-12 + 7

                        fifth at bass
2   t   4               t-12 + 7


3   t   4           7   t-12 + 11

"""
class MidiChord:
    """
    We can iterate over the midi note produced by the chord type and width
    """
    def __init__(self, tonic=60, name='Major', inversion=0, width=3):
        self.name = name
        self.midi_notes = [] # a list of midi chord notes sans tonic
        width -= 1 # only generate the other chord notes
        chords = ChordInfo()
        intervals = chords.get_intervals(name)
        if intervals is None:
            log.critical(f'Unrecognized chord name {name}')
            raise Exception(f'Unrecognized chord name: {name}')

        #log.info(f'Chord: {name}, intervals: {intervals}')

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
        self.update = True # set if we need to update delays
        self.chord_names = ChordInfo().get_names()
        self.chord_index = self.settings.get('ChordEffectName', 0) # major chord
        # default a 3 note major chord 
        self.new_chord_index = self.chord_index
        self.chord_width = self.settings.get('ChordEffectWidth', 3) # triad
        self.new_chord_width = self.chord_width

        # for strum
        self.strummer = Strummer()
        strum_delay = self.settings.get('ChordEffectStrumDelay', 0) # 0 = no strum
        if strum_delay:
            self.strummer.set_delay(strum_delay)
            self.strummer.run()

        # do last
        if self.cc_controls is not None:
            self.add_controls()

    def __str__(self):
        return f'Chord effect - Type: {self.chord_name}, Notes: {self.chord_width}'

    def panic(self):
        """
        cancels all future notes
        """
        self.strummer.stop()
           

    def get_chord_name_label(self, index):
        if index >= len(self.chord_names):
            return 0
        return self.chord_names[index]


    def add_controls(self):
        """
        called at init to add cc controls map
        """
        # VI25 Alesis controller CC knobs start with 21
        # cc defaults must be unique
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

        self.cc_controls.add(name='ChordEffectStrumDelayControlCC',
                                 cc_default=24,
                                 control_callback=self.control_chord_strum_delay,
                                 min=0,
                                 max=30) # in tenths of seconds

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

        #self.panic() # halts notes in progress
        self.new_chord_index = control
        self.settings.set('ChordEffectName', control)
        #log.info(f"Chord: {self.chord_names[self.new_chord_index]}")

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
        self.settings.set('ChordEffectWidth', control)
        #log.info(f"Chord width: {self.new_chord_width}")

    def control_chord_strum_delay(self, control):
        """
        A All controls are mapped to the value range set in add_controls
        """
        if control > 0 and self.strummer.is_running() == False:
            self.strummer.run() # start strum clock
            
            

        if control == 0 and self.strummer.is_running() == True:
            self.strummer.stop()  # stop strum clock

        self.strummer.set_delay(control)  
        self.settings.set('ChordEffectStrumDelay', control)
        #log.info(f"Chord strum delay: {control}")


    def run(self, tick, midiout, message):
        """
        generate the added notes for the chord
        """
        # if we change in the middle of a chord playing we get stuck notes
        if self.chord_index != self.new_chord_index or self.chord_width != self.new_chord_width:
            self.chord_index = self.new_chord_index
            self.chord_width = self.new_chord_width
            self.strummer.purge()
            self.purge(midiout) # turns off pending notes. 

        midiout.send_message(message)  # send original note event

        onote = MidiNoteMessage(message)
        try:
            chord = MidiChord(tonic=onote.note, name=self.chord_names[self.chord_index], width=self.chord_width)
        except:
            return

        num = 1
        for note in chord.notes():
            onote.note = note
            message = onote.get_message()
            self.add_note_on_event(message) # keeps track of note on events if we need to purge

            if self.strummer.is_running() == True:
               self.strummer.add(num, message, midiout)
               num += 1
            else:
                midiout.send_message(message)

        
       
class Strummer:
    """
    fires off a thread to play delayed strum notes
    Runs at 10 msec intervals
    """
    def __init__(self):
        
        self.tick_time = 0.01 # 10 msec
        self.running = False
        self.note_manager = NoteManager() 
        self.midiout = None
        self.tick = 0
        self.delay_ticks = 0

    def set_delay(self, ticks):
        self.delay_ticks = ticks

    def add(self, num, message, midiout):
        play_tick = self.tick + (num * self.delay_ticks)
        #log.info(f'Strummer add: {play_tick}')
        self.note_manager.add(play_tick, message)
        self.midiout = midiout

    def thread(self):
        while True:
            if self.running == False:
                #log.info('Exiting Strummer')
                return # exit thread

            start = time.perf_counter()

            self.note_manager.run(self.tick, self.midiout)
            self.tick += 1 # count forever
            
            time_to_sleep = self.tick_time - (time.perf_counter() - start) # subtract off time we worked
            if time_to_sleep < 0.0:
                log.error('Strummer work took too long')
                time_to_sleep = self.tick_time # need to sleep else get stuck in this thread forever

            # log.info(f'Internal clock tick: {self.tick}'
            time.sleep(time_to_sleep)

    def run(self):
        #log.info('Starting Strummer ')
        self.running = True
        timerThread = threading.Thread(target=self.thread)
        timerThread.start()

    def is_running(self):
        return self.running

    def purge(self):
        self.note_manager.purge()

    def stop(self):
        self.purge()
        self.running = False

