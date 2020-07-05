"""
 Copyright (C) 2020 Brian R. Gunnison
 
 This file is part of MIDI BEAT project
 
 MIDI BEAT can not be copied and/or distributed without the express
 permission of Brian R. Gunnison
"""
import sys
import os
import time
import logging



logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from ui.mainapp import RootWidget
from midiapps.midi_beat import MidiBeatEffect

import kivy
kivy.require('1.11.1')


from kivy.app import App


    
class BeatWidget(RootWidget):

    def __init__(self, **kwargs):
        super(BeatWidget, self).__init__(title='MidiBeat', effect=MidiBeatEffect)
   
    def update_effect_controls(self):
        """
        called at startup to set the effect specific controls
        each effect control has a label, a CCBox a current value and a slider
        current value can be a number or text
        """
        # create a database of effect ids, funcs etc, used for setup and control
        # this control selects a beat which is then controlled by what follows
        self.effect_controls['BeatEffectBeatSelectControlCC'] = {'control_name':'BeatEffectBeatSelectControlCC',
                                                                'settings_name':'BeatEffectBeatSelect',
                                                                'slider_id':self.ids.BeatEffectBeatSelectSlider, # update slider
                                                                'value_id':self.ids.BeatEffectBeatSelectValue, # update text
                                                                'control_cc_id':self.ids.BeatEffectBeatSelectControlCC,
                                                                'update_function':self.effect.control_beat_select} 

        self.update_effect_control('BeatEffectBeatSelectControlCC')

        # to have multiple objects we replace the settings object specifier with 'XObject'
        # this is replaced with the current settings object number from the effect
        self.effect_controls['BeatEffectOctaveControlCC'] =   {'control_name':'BeatEffectOctaveControlCC',
                                                                   'settings_name':'BeatEffectOctaveXObject',
                                                                   'slider_id':self.ids.BeatEffectOctaveSlider, # update slider
                                                                   'value_id':self.ids.BeatEffectOctaveValue, # update text
                                                                   'control_cc_id':self.ids.BeatEffectOctaveControlCC,
                                                                   'update_function':self.effect.control_octave} 

        self.update_effect_control('BeatEffectOctaveControlCC')

        self.effect_controls['BeatEffectNoteControlCC'] =     {'control_name':'BeatEffectNoteControlCC',
                                                                   'settings_name':'BeatEffectNoteXObject',
                                                                   'slider_id':self.ids.BeatEffectNoteSlider, # update slider
                                                                   'value_id':self.ids.BeatEffectNoteValue, # update text
                                                                   'control_cc_id':self.ids.BeatEffectNoteControlCC,
                                                                   'text_function':self.effect.get_note_label, # only if control has text values instead of a number
                                                                   'update_function':self.effect.control_note} 

        self.update_effect_control('BeatEffectNoteControlCC')

        self.effect_controls['BeatEffectLoudControlCC'] = {'control_name':'BeatEffectLoudControlCC',
                                                                   'settings_name':'BeatEffectLoudXObject',
                                                                   'slider_id':self.ids.BeatEffectLoudSlider, # update slider
                                                                   'value_id':self.ids.BeatEffectLoudValue, # update text
                                                                   'control_cc_id':self.ids.BeatEffectLoudControlCC,
                                                                   'update_function':self.effect.control_loud} 

        self.update_effect_control('BeatEffectLoudControlCC')

        self.effect_controls['BeatEffectLoopControlCC'] = {'control_name':'BeatEffectLoopControlCC',
                                                                   'settings_name':'BeatEffectLoopXObject',
                                                                   'slider_id':self.ids.BeatEffectLoopSlider, # update slider
                                                                   'value_id':self.ids.BeatEffectLoopValue, # update text
                                                                   'control_cc_id':self.ids.BeatEffectLoopControlCC,
                                                                   'update_function':self.effect.control_loop} 

        self.update_effect_control('BeatEffectLoopControlCC')

        self.effect_controls['BeatEffectBeatsControlCC'] = {'control_name':'BeatEffectBeatsControlCC',
                                                                   'settings_name':'BeatEffectBeatsXObject',
                                                                   'slider_id':self.ids.BeatEffectBeatsSlider, # update slider
                                                                   'value_id':self.ids.BeatEffectBeatsValue, # update text
                                                                   'control_cc_id':self.ids.BeatEffectBeatsControlCC,
                                                                   'update_function':self.effect.control_beats} 

        self.update_effect_control('BeatEffectBeatsControlCC')

        self.effect_controls['BeatEffectRotateControlCC'] = {'control_name':'BeatEffectRotateControlCC',
                                                                   'settings_name':'BeatEffectRotateXObject',
                                                                   'slider_id':self.ids.BeatEffectRotateSlider, # update slider
                                                                   'value_id':self.ids.BeatEffectRotateValue, # update text
                                                                   'control_cc_id':self.ids.BeatEffectRotateControlCC,
                                                                   'update_function':self.effect.control_rotate} 

        self.update_effect_control('BeatEffectRotateControlCC')


    def get_help_text(self):
        return 'Welcome to VIRTUAL ROBOT MIDI BEAT. \
To get started quickly: on the left are navigation buttons, \
press “MIDI” and select a MIDI output device. \
This app will send beats out to this this device. \
Set the clock to “INTERNAL”. '
"""
Via the “BEAT” navigator button \
set the beats to "on". A default 4 beats per 16 beat loop will start playing with a C2 note. \
Select the beat you wish to modify with the "BEAT SELECT" slider. \ 
The green boxes next to buttons or sliders are the MIDI controller that can also change the setting. \
Click inside the box and move the MIDI controller to learn. Or change the number \
by typing a new one. For detailed help read the manual at the link above. \
Also please check out the other VIRTUAL ROBOT MIDI apps at the website.
"""




class MainBeatApp(App):
    def build(self):
        self.title = 'VIRTUAL ROBOT MIDI BEAT'
        self.icon = 'media/logoico.png'
        self.root_widget = BeatWidget()
        return  self.root_widget

    def on_stop(self):
        log.info('on_stop')
        self.root_widget.destroy()
        log.info('on_stop exited')


if __name__ == '__main__':
    app = MainBeatApp()
    app.run() 
    log.info('run exited')
   
