"""
 Copyright (C) 2020 Brian R. Gunnison
 
 This file is part of MIDI EFFECTS project
 
 MIDI EFFECTS can not be copied and/or distributed without the express
 permission of Brian R. Gunnison
"""
import os
import sys
import logging

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


class MidiEffectManager:

    def __init__(self, effect, midi_manager):
        self.midi_manager = midi_manager      
        self.effect_enabled = False
        self.effect = effect
        # button CCs are mapped to to enable (for example) the effect
        self.effect_manager_controls = {
                        48:{'func':self.enable_effect_control, 'name':f'Enable {self.effect.get_name()}'}
                       }

    def enable_effect_control(self, control): 
        if control == 0:
            self.effect_enabled = False
        else:
            self.effect_enabled = True


    def run(self):
        self.midi_manager.register_note_callback(self.note_callback)
        self.midi_manager.register_clock_callback(self.clock_callback)
        self.midi_manager.register_control_callback(self.control_callback)
        self.midi_manager.clock_source.run()
        self.midi_manager.midiin.run()
        log.info('Running')

    def apply_effect(self, tick, message):
        """
        A effect object acts on the incoming note
        and may add note events to the note manager to play in the future
        """
        if self.effect_enabled == False:
            self.midi_manager.midiout.send_message(message)  # send original note event
            return

        self.effect.run(tick, self.midi_manager.midiout, message)


    def note_callback(self, message, clock_source):
        """
        invoked by our input when a note is on or off
        """ 
        tick = clock_source.get_tick()
        #log.info(f"Note callback: {message}, {tick}")
        self.apply_effect(tick, message)         # may add  note events for the future
        self.effect.note_manager.run(tick, self.midi_manager.midiout)        


    def clock_callback(self, tick, data):
        """
        called at midi clock intervals or at 60 bpm every 42 msec - 24 times per quarter note
        here we run the note manager and it sends or stops notes as queued
        This runs quite fast so no delays...
        """
        #log.info(f"Clock callback: {tick}")
        self.effect.note_manager.run(tick, self.midi_manager.midiout)
    
    def control_callback(self, cc, control):
        """
        A cc button switches effects or
        An effect has controllable parms via CC knobs
        The app maps the CC to the parm(s). This callback has the CC number and control  (0 - 127)
        We use the CC to get the effect parm function and call it.
        """
        # intercept effect manager controls first
        manage_effect_info = self.effect_manager_controls.get(cc)
        if manage_effect_info is not None:
            manage_effect_info['func'](control)
            return

        control_info = self.effect.control_map.get(cc)
        if control_info is None:
            return

        control_info['func'](control)


if __name__ == '__main__':
    app = MidiEffectManager(EchoEffect())
    app.run()
    while True:
        time.sleep(0.2)

    app.panic()