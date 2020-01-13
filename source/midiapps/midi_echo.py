"""
MIDI echo effect
"""
import os
import sys
import math
import logging


sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

from common.midi import *


class MidiEchoEffect(Effect):
    def __init__(self):
        self.name = 'Echo'
        self.note_manager = NoteManager()
        self.update = True # set if we need to update delays
        self.delay_start_ticks = 24 # this is a quarter note
        self.delay_types = ['linear', 'exp_slow_start', 'exp_fast_start']
        self.delay_type = self.delay_types[0]
        self.delays = []    # a list of ticks for each echo (number of echoes)
        self.new_delays = self.delays
        self.echoes = 3
        self.end_velocity = 10 #we linear ramp velocity down to this level
        self.calc_delays() # init echoes
        # VI25 Alesis controller CC knobs start with 21
        self.control_map = {    21:{'func':self.control_delay_type,'name':'Delay Type'},
                                22:{'func':self.control_echoes, 'name':'Echoes'},
                                23:{'func':self.control_delay_tick, 'name':'Delay'}
                           } 

    def __str__(self):
        return f'Echo effect - Echoes: {self.echoes}, Type: {self.delay_type}, Delay: {self.delay_start_ticks}'

    def set_midi_out(self, midiout):
        self.note_manager.set_midi_out(midiout)

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
        All controls are 0 - 127 per CC
        """
        t = self.control_to_selection(self.delay_types, control)
        self.delay_type = self.delay_types[t]
        self.calc_delays()
        log.info(f"Delay type: {self.delay_type}")


    def control_echoes(self, control):
        """
        All controls are 0 - 127 per CC
        """
        control += 1
        control /= 4
        self.echoes = int(control)
        self.calc_delays()
        log.info(f"echoes: {self.echoes}")

    def control_delay_tick(self, control):
        """
        All controls are 0 - 127 per CC
        """
        self.delay_start_ticks = control
        self.calc_delays()
        log.info(f"delay ticks: {self.delay_start_ticks}")

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
        for i, d in enumerate(self.delays):
            note.velocity = round(ov - ((i + 1) * dv))
            if note.velocity < self.end_velocity:
                break
            self.note_manager.add(d+tick, note.get_message())
            


