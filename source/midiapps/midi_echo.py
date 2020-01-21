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

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

from common.midi import MidiNoteMessage, MidiConstants
from common.upper_class_utils import Effect, NoteManager


class MidiEchoEffect(Effect):
    def __init__(self, settings, cc_controls=None):
        super().__init__(settings, cc_controls)
        self.name = 'Echo'
        self.note_manager = NoteManager()
        self.update = True # set if we need to update delays
        self.delay_start_ticks = self.settings.get('EchoEffectDelayStartTicks',24) # this is a quarter note
        self.delay_types = ['linear', 'exp_slow_start', 'exp_fast_start']
        self.delay_type = self.settings.get('EchoEffectDelayType', self.delay_types[0]) # store the string
        self.delays = []    # a list of ticks for each echo (number of echoes)
        self.new_delays = self.delays
        self.echoes = self.settings.get('EchoEffectNumberEchos', 3)
        self.end_velocity = self.settings.get('EchoEffectEndVelocity', 10) # we linear ramp velocity down to this level
        self.calc_delays() # init echoes
        if self.cc_controls is not None:
            self.add_controls()

    def __str__(self):
        return f'Echo effect - Echoes: {self.echoes}, Type: {self.delay_type}, Delay: {self.delay_start_ticks}'

    def get_ui_controls(self):
        """
        returns a dict of UI control info to populate the UI
        used at startup 
        """

    def add_controls(self):
        """
        called at init to add cc controls map
        """
        # VI25 Alesis controller CC knobs start with 21
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
        self.update = True
        self.new_delays = []
        if self.delay_type is 'linear':
            for i in range(self.echoes):
                self.new_delays.append((i+1) * self.delay_start_ticks)
            return

       
        if 'exp' in self.delay_type:
            s = 0.2
            e = 4
            a = (e - s)/float(self.echoes)
            for i in range(self.echoes):
                v = 0.2 + ((i+1) * a)
                f = (1.61 + math.log(v))/2.996
                delay = round(self.delay_start_ticks * f)
                self.new_delays.append(delay)

            if self.delay_type is 'exp_slow_start':
                log.info(f"delays: {self.new_delays}")
                return

            if self.delay_type is 'exp_fast_start':
                """ wrong!! 
                self.new_delays.reverse()
                s = 0
                nd = []
                for i, v in enumerate(self.new_delays):
                    s += v
                    nd.append(s)

                self.new_delays = nd
                log.info(f"delays: {self.new_delays}")

                """
                return


    def control_delay_type(self, control):
        """
        index to delay type
        """
        if control >= len(self.delay_types):
            log.error('delay type index too big')
            return

        self.delay_type = self.delay_types[control]
        self.calc_delays()
        self.settings.set('EchoEffectDelayType', self.delay_type)
        log.info(f"Delay type: {self.delay_type}")


    def control_echoes(self, control):
        """
        1 - 32
        """
        self.echoes = control
        self.calc_delays()
        log.info(f"echoes: {self.echoes}")

    def control_delay_tick(self, info, control):
        """
        All controls are 0 - 127 per CC
        """
        self.delay_start_ticks = control
        self.calc_delays()
        log.info(f"delay ticks: {self.delay_start_ticks}")


    def control_end_velocity(self, control):
        """
        1 - 127
        """
        self.control_end_velocity = control


    def run(self, tick, midiout, message):
        """
        note events are added to note manager at future times
        """
        midiout.send_message(message)  # send original note event

        note = MidiNoteMessage(message)
        if note.velocity <= self.end_velocity:
            return

        # if we change number of echoes in the middle of echoing notes
        # we could miss note off events. 
        if self.update:
            if self.note_manager.empty():
                self.delays = self.new_delays
                self.update = False


        # divide the velocity range to get to min from original v
        ov = note.velocity
        dv = (ov - self.end_velocity)/float(len(self.delays))
        for i, delay in enumerate(self.delays):
            note.velocity = round(ov - ((i + 1) * dv))

            if note.velocity > MidiConstants().CC_MAX:
                note.velocity = MidiConstants().CC_MAX

            if note.velocity < self.end_velocity:
                break

            self.note_manager.add(delay + tick, note.get_message())
            


