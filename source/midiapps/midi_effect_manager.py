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
                        #cc                     called when changed from midi port       calls up to change UI
                        48:{'name':'Enable', 'func':self.enable_effect_control, 'callback':None}
                       }

    def register_cc_callback(self, name, callback):
        """
        adds a callback to the UI to change widgets during a cc
        """
        for cc, info in self.effect_manager_controls.items():
            if info.get('name') == name:
                info['callback'] = callback
                break

    def enable_effect_control(self, info, control): 
        """
        called when its cc changes
        """
        if control == 0: 
            on = False
        else:
            on = True

        self.effect_enable(on)
        callback = info.get('callback')
        if callback is not None:
            callback(on) # callback to UI

    def effect_enable(self, on):
        log.info(f'Effect: {self.effect.get_name()} is {on}')
        self.effect_enabled = on

    def remap_cc(self, name, cc):
        """
        find the named cc info and change its cc number
        """
        for oldcc, info in self.effect_manager_controls.items():
            if info.get(name) is not None:
                self.effect_manager_controls[cc] = info
                del self.effect_manager_controls[oldcc]
                return True

        return False



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
        info = self.effect_manager_controls.get(cc)
        if info is not None:
            #log.info(f'cc: {cc}, {info["name"]}')
            info['func'](info, control)
            return

        info = self.effect.control_map.get(cc)
        if info is None:
            return

        info['func'](info, control)


if __name__ == '__main__':
    app = MidiEffectManager(EchoEffect())
    app.run()
    while True:
        time.sleep(0.2)

    app.panic()