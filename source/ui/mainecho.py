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



logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from ui.mainapp import RootWidget
from midiapps.midi_echo import MidiEchoEffect

import kivy
kivy.require('1.11.1')


from kivy.app import App


    
class EchoWidget(RootWidget):

    def __init__(self, **kwargs):
        super(EchoWidget, self).__init__(title='MidiEcho', effect=MidiEchoEffect)
   
    def update_effect_controls(self):
        """
        called at startup to set the effect specific controls
        each effect control has a label, a CCBox a current value and a slider
        current value can be a number or text
        """
        # create a database of effect ids, funcs etc, used for setup and control
        self.effect_controls['EchoEffectDelayTypeControlCC'] = {'control_name':'EchoEffectDelayTypeControlCC',
                                                                'settings_name':'EchoEffectDelayType',
                                                                'slider_id':self.ids.EchoEffectDelayTypeSlider, # update slider
                                                                'value_id':self.ids.EchoEffectDelayTypeValue, # update text
                                                                'control_cc_id':self.ids.EchoEffectDelayTypeControlCC,
                                                                'text_function':self.effect.get_delay_type_label, # only if control has text values instead of a number
                                                                'update_function':self.effect.control_delay_type} 

        self.update_effect_control('EchoEffectDelayTypeControlCC')

        self.effect_controls['EchoEffectNumberEchoesControlCC'] = {'control_name':'EchoEffectNumberEchoesControlCC',
                                                                   'settings_name':'EchoEffectNumberEchoes',
                                                                   'slider_id':self.ids.EchoEffectNumberEchoesSlider, # update slider
                                                                   'value_id':self.ids.EchoEffectNumberEchoesValue, # update text
                                                                   'control_cc_id':self.ids.EchoEffectNumberEchoesControlCC,
                                                                   'update_function':self.effect.control_echoes} 

        self.update_effect_control('EchoEffectNumberEchoesControlCC')

        self.effect_controls['EchoEffectDelayStartTicksControlCC'] = {'control_name':'EchoEffectDelayStartTicksControlCC',
                                                                   'settings_name':'EchoEffectDelayStartTicks',
                                                                   'slider_id':self.ids.EchoEffectDelayStartTicksSlider, # update slider
                                                                   'value_id':self.ids.EchoEffectDelayStartTicksValue, # update text
                                                                   'control_cc_id':self.ids.EchoEffectDelayStartTicksControlCC,
                                                                   'update_function':self.effect.control_delay_tick} 

        self.update_effect_control('EchoEffectDelayStartTicksControlCC')

        self.effect_controls['EchoEffectEndVelocityControlCC'] = {'control_name':'EchoEffectEndVelocityControlCC',
                                                                   'settings_name':'EchoEffectEndVelocity',
                                                                   'slider_id':self.ids.EchoEffectEndVelocitySlider, # update slider
                                                                   'value_id':self.ids.EchoEffectEndVelocityValue, # update text
                                                                   'control_cc_id':self.ids.EchoEffectEndVelocityControlCC,
                                                                   'update_function':self.effect.control_end_velocity} 

        self.update_effect_control('EchoEffectEndVelocityControlCC')

  
    def get_help_text(self):
        return 'Welcome to VIRTUAL ROBOT MIDI ECHO. \
To get started quickly: on the left are navigation buttons, \
press “MIDI” and select a MIDI input device. \
This app will echo the notes coming in from this device. Select an output \
device to hear the echoed notes. Set the clock to \
“INTERNAL”. Via the “ECHO” navigator button \
set the effect to "on". Generate a input \
note and you should hear the echoes on the output device. The green boxes \
next to buttons or sliders are the MIDI controller that can also change the setting. \
Click inside the box and move the MIDI controller to learn. Or change the number \
by typing a new one. For detailed help read the manual at the link above. \
Also please check out the other VIRTUAL ROBOT MIDI apps at the website.' 




class MainEchoApp(App):
    def build(self):
        self.title = 'VIRTUAL ROBOT MIDI ECHO'
        self.icon = 'media/logoico.png'
        self.root_widget = EchoWidget()
        return  self.root_widget

    def on_stop(self):
        log.info('on_stop')
        self.root_widget.destroy()
        log.info('on_stop exited')


if __name__ == '__main__':
    app = MainEchoApp()
    app.run() 
    log.info('run exited')
   
