"""
 Copyright (C) 2020 Brian R. Gunnison
 
 This file is part of MIDI ECHO project
 
 MIDI ECHO can not be copied and/or distributed without the express
 permission of Brian R. Gunnison
"""
import os
import sys
import math
import logging


sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

logging.basicConfig(level=logging.ERROR)
log = logging.getLogger(__name__)

from common.midi import MidiNoteMessage, MidiConstants
from common.upper_class_utils import NoteManager
from midiapps.midi_effect_manager import Effect


class MidiEchoEffect(Effect):
    def __init__(self, settings, cc_controls=None):
        super().__init__(settings, cc_controls)
        self.name = 'Echo'
        self.note_manager = NoteManager()
        self.update = True # set if we need to update delays
        self.delay_start_ticks = self.settings.get('EchoEffectDelayStartTicks',24) # this is a quarter note
        self.delay_types = ['LINEAR', 'EXP SLOW', 'EXP FAST']   # seen in ui
        self.delay_type = self.settings.get('EchoEffectDelayType', 0) 
        self.delays = []    # a list of ticks for each echo (number of echoes)
        self.new_delays = self.delays
        self.echoes = self.settings.get('EchoEffectNumberEchoes', 3)
        self.end_velocity = self.settings.get('EchoEffectEndVelocity', 10) # we linear ramp velocity down to this level
        self.calc_delays() # init echoes
        if self.cc_controls is not None:
            self.add_controls()

    def __str__(self):
        return f'Echo effect - Echoes: {self.echoes}, Type: {self.delay_type}, Delay: {self.delay_start_ticks}'

    def panic(self):
        """
        cancels all echoes
        """
        self.update = True # catches this in run and purges pending notes. 

    def get_delay_type_label(self, index):
        if index >= len(self.delay_types):
            return 0
        return self.delay_types[index]
       
    def add_controls(self):
        """
        called at init to add cc controls map
        """
        # VI25 Alesis controller CC knobs start with 21
        # cc defaults must be unique
        self.cc_controls.add(name='EchoEffectDelayTypeControlCC',
                                 cc_default=22,
                                 control_callback=self.control_delay_type,
                                 min=0,
                                 max=len(self.delay_types) - 1)

        self.cc_controls.add(name='EchoEffectNumberEchoesControlCC',
                                 cc_default=23,
                                 control_callback=self.control_echoes,
                                 min=1,
                                 max=32)

        self.cc_controls.add(name='EchoEffectDelayStartTicksControlCC',
                                 cc_default=24,
                                 control_callback=self.control_delay_tick,
                                 min=0,
                                 max=MidiConstants().CC_MAX)

        self.cc_controls.add(name='EchoEffectEndVelocityControlCC',
                                 cc_default=25,
                                 control_callback=self.control_end_velocity,
                                 min=0,
                                 max=MidiConstants().CC_MAX)


    def calc_delays(self):
        """
        based on settings we can calculate the delays
        and return it in a list, this the number of echoes and the delay of each
        """
        delay_type_str = self.delay_types[self.delay_type]
        self.update = True
        self.new_delays = []
        self.panic()    # stop all ongoing notes to start fresh with new parms (might be an option)
        if delay_type_str is 'LINEAR':
            for i in range(self.echoes):
                self.new_delays.append((i+1) * self.delay_start_ticks)
            return

        if 'EXP' in delay_type_str:
            s = 0.2
            e = 4
            a = (e - s)/float(self.echoes)
            for i in range(self.echoes):
                v = 0.2 + ((i+1) * a)
                f = (1.61 + math.log(v))/2.996
                delay = round(self.delay_start_ticks * f)
                self.new_delays.append(delay)

            if 'SLOW' in delay_type_str:
                #log.info(f"slow delays: {self.new_delays}")
                return

            if 'FAST' in delay_type_str:
             
                hi = self.new_delays[-1]
                self.new_delays.reverse()
                self.new_delays = [hi - d for d in self.new_delays]
                #log.info(f"fast delays: {self.new_delays}")
                return


    def control_delay_type(self, control):
        if control >= len(self.delay_types):
            log.error('Echo delay types control too big')
            return

        self.delay_type = control
        self.calc_delays()
        self.settings.set('EchoEffectDelayType', self.delay_type)
       # log.info(f"Delay type: {self.delay_types[self.delay_type]}")


    def control_echoes(self, control):
        """
        1 - 32
        """
        self.echoes = control
        self.calc_delays()
        self.settings.set('EchoEffectNumberEchoes', self.echoes)
        #log.info(f"echoes: {self.echoes}")

    def control_delay_tick(self, control):
        """
        1 - 127
        """
        self.delay_start_ticks = control
        self.settings.set('EchoEffectDelayStartTicks', self.delay_start_ticks)
        self.calc_delays()
       # log.info(f"delay ticks: {self.delay_start_ticks}")


    def control_end_velocity(self, control):
        """
        1 - 127
        """
        self.end_velocity = control
        self.settings.set('EchoEffectEndVelocity', self.end_velocity)



    def run(self, tick, midiout, message):
        """
        note events are added to note manager at future times
        """
        midiout.send_message(message)  # send original note event

        note = MidiNoteMessage(message)
        end_velocity = self.end_velocity
        if note.velocity <= end_velocity:
            end_velocity = note.velocity

        # if we change number of echoes in the middle of echoing notes
        # we could miss note off events. 
        if self.update:
            self.purge(midiout) # turns off pending notes. 
            self.note_manager.purge()
            self.delays = self.new_delays
            self.update = False

        #log.info(f'Tick: {tick}, msg: {message}')
        # divide the velocity range to get to min from original v
        ov = note.velocity
        dv = (ov - end_velocity)/float(len(self.delays))
        for i, delay in enumerate(self.delays):
            note.velocity = round(ov - ((i + 1) * dv))

            if note.velocity > MidiConstants().CC_MAX:
                note.velocity = MidiConstants().CC_MAX

            if note.velocity < end_velocity:
                break

            self.add_note_on_event(note.get_message()) # keeps track of note on events if we need to purge
            self.note_manager.add(delay + tick, note.get_message())
            


