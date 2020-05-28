"""
 Copyright (C) 2020 Brian R. Gunnison
 
 This file is part of MIDI ECHO project
 
 MIDI ECHO can not be copied and/or distributed without the express
 permission of Brian R. Gunnison
"""
import sys
import os
import time
import logging



logging.basicConfig(level=logging.ERROR)
log = logging.getLogger(__name__)

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from ui.mainapp import RootWidget
from midiapps.midi_chord import MidiChordEffect

import kivy
kivy.require('1.11.1')


from kivy.app import App


    
class ChordWidget(RootWidget):

    def __init__(self, **kwargs):
        super(ChordWidget, self).__init__(title='MidiChord', effect=MidiChordEffect, use_clock=False)
   
    def update_effect_controls(self):
        """
        called at startup to set the effect specific controls
        each effect control has a label, a CCBox a current value and a slider
        current value can be a number or text
        """
        # create a database of effect ids, funcs etc, used for setup and control
        self.effect_controls['ChordEffectNameControlCC'] = {'control_name':'ChordEffectNameControlCC',
                                                                'settings_name':'ChordEffectName',
                                                                'slider_id':self.ids.ChordEffectNameSlider, # update slider
                                                                'value_id':self.ids.ChordEffectNameValue, # update text
                                                                'control_cc_id':self.ids.ChordEffectNameControlCC,
                                                                'text_function':self.effect.get_chord_name_label, # only if control has text values instead of a number
                                                                'update_function':self.effect.control_chord_name} 

        self.update_effect_control('ChordEffectNameControlCC')

        self.effect_controls['ChordEffectWidthControlCC'] = {'control_name':'ChordEffectWidthControlCC',
                                                                   'settings_name':'ChordEffectWidth',
                                                                   'slider_id':self.ids.ChordEffectWidthSlider, # update slider
                                                                   'value_id':self.ids.ChordEffectWidthValue, # update text
                                                                   'control_cc_id':self.ids.ChordEffectWidthControlCC,
                                                                   'update_function':self.effect.control_chord_width} 

        self.update_effect_control('ChordEffectWidthControlCC')

        self.effect_controls['ChordEffectStrumDelayControlCC'] = {'control_name':'ChordEffectStrumDelayControlCC',
                                                                   'settings_name':'ChordEffectStrumDelay',
                                                                   'slider_id':self.ids.ChordEffectStrumDelaySlider, # update slider
                                                                   'value_id':self.ids.ChordEffectStrumDelayValue, # update text
                                                                   'control_cc_id':self.ids.ChordEffectStrumDelayControlCC,
                                                                   'update_function':self.effect.control_chord_strum_delay} 

        self.update_effect_control('ChordEffectStrumDelayControlCC')

  
    def get_help_text(self):
        return 'Welcome to VIRTUAL ROBOT MIDI CHORD. \
To get started quickly: on the left are navigation buttons, \
press “MIDI” and select a MIDI input device. \
This app will play a chord based on the notes coming in from this device. Select an output \
device to hear the chord notes. Generate a input \
note and you should hear the chord on the output device. The green boxes \
next to buttons or sliders are the MIDI controller that can also change the setting. \
Click inside the box and move the MIDI controller to learn. Or change the number \
by typing a new one. For detailed help read the manual at the link above. \
Also please check out the other VIRTUAL ROBOT MIDI apps at the website.'



class MainChordApp(App):
    def build(self):
        self.title = 'VIRTUAL ROBOT MIDI CHORD'
        self.icon = 'media/logoico.png'
        self.root_widget = ChordWidget()
        return  self.root_widget

    def on_stop(self):
        log.info('on_stop')
        self.root_widget.destroy()
        log.info('on_stop exited')


if __name__ == '__main__':
    app = MainChordApp()
    app.run() 
    log.info('run exited')
   
