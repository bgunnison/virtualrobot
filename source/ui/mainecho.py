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

help_text = 'Welcome to VirtualRobots MIDI ECHO. \
To get started quickly on the left are navigating buttons, \
press “MIDI” and select a MIDI input device. \
This app will echo the notes coming in here. Then select an output \
device so you can hear the echoed notes. The clock should be set to \
“INTERNAL” to make sure we get echoes. Via the “ECHO” navigator button \
go to the “ECHO” settings screen and enable the effect. Generate a input \
note and you should hear the echoes on the output device. The green boxes \
next to buttons or sliders are the MIDI controller that can change the setting. \
Click inside the box and move the MIDI controller to learn. Or change the number \
by typing a new one. If you look carefully at the right side of the MIDI output selection \
The skull is a MIDI panic button. Press this to cancel any stuck notes or echoes \
that are going on too long. For detailed help read the manual at the link above. \
Also please check out the other VirtualRobot MIDI apps at the website.' 


logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from midiapps.midi_echo import MidiEchoEffect
from midiapps.midi_effect_manager import MidiEffectManager
from common.midi import MidiManager, MidiConstants
from common.upper_class_utils import Settings
#from common.license import License

import kivy
kivy.require('1.11.1')

from kivy.config import Config
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')
Config.set('graphics', 'resizable', False)
Config.set('graphics', 'multisamples', 8)
Config.set('kivy','window_icon','media/logo.ico') # no work...


from kivy.app import App
from kivy.core.window import Window
from kivy.properties import StringProperty
from kivy.uix.screenmanager import ScreenManager, Screen, RiseInTransition
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Color, Rectangle
from kivy.uix.spinner import Spinner
from kivy.uix.slider import Slider
from kivy.uix.popup import Popup
from kivy.uix.image import Image
from kivy.clock import Clock

class TitleBoxLayout(BoxLayout):
    pass

class NavButtons(BoxLayout):
    pass

class LogoZipped(BoxLayout):
    pass

class MainScreenManager(ScreenManager):
    pass
           
class MidiScreen(Screen):
    pass 

class EchoScreen(Screen):
    pass
       
class LiveScreen(Screen):
     pass

class HelpScreen(Screen):
    pass


class CCControlInput(TextInput):
    pass


class ScrollableLabel(ScrollView):
    pass

    
gsettings = None

class RootWidget(BoxLayout):

    def __init__(self, **kwargs):
        super(RootWidget, self).__init__(**kwargs)

        self.settings = Settings('MidiEcho')    # our persistant settings
        global gsettings
        gsettings = self.settings   # so when the app exits we save

        self.midi_manager = MidiManager(self.settings)
        self.effect = MidiEchoEffect(self.settings, self.midi_manager.cc_controls)
        self.effect_manager = MidiEffectManager(self.settings, self.effect, self.midi_manager)
        self.effect_controls = {} # dict keyd by effect control name with ui ids to update if we get a CC control
        # restore screen in settings
        screen = self.settings.get('start_screen', 'screen_midi')
        if 'midi' in screen:
            but = self.ids.nav_midi
        if 'echo' in screen:
            but = self.ids.nav_echo
        #if 'live' in screen:
        #    but = self.ids.nav_live
        if 'help' in screen:
            but = self.ids.nav_help

        self.nav_button_pressed(but, screen)

        self.update_midi_screen()

        self.update_echo_screen()

        # call last
        self.effect_manager.run()

        self.start_activity_LEDs()

    def bold(self, text):
        return '[b]' + text + '[/b]' # markup must be true, this is our style plus CAPS

    def midi_panic(self, dt):
        self.effect.panic()
        self.midi_manager.panic()

    def start_midi_panic(self, but):       
        Clock.schedule_once(self.midi_panic)               

    def end_midi_panic(self, but):
        pass

    def update_midi_screen(self):
        """
        called at startup
        """
        self.update_port_selections()
        self.update_clock_selections()

        # reopen midi ports if in settings
        midi_port = self.settings.get('midi_in_port')
        if midi_port is not None:
            if midi_port in self.midi_manager.get_midi_in_ports():
                self.ids.midi_port_in.text = midi_port
                self.select_midi_input_port(self.ids.midi_port_in)

        midi_port = self.settings.get('midi_out_port')
        if midi_port is not None:
            if midi_port in self.midi_manager.get_midi_out_ports():
                self.ids.midi_port_out.text = midi_port
                self.select_midi_output_port(self.ids.midi_port_out)


    def update_echo_screen(self):
        self.midi_manager.cc_controls.register_ui_callback('EffectEnableControlCC', self.ui_effect_on)
        cc_str = self.midi_manager.cc_controls.get_cc_str('EffectEnableControlCC')
        self.ids.EffectEnableControlCC.text = cc_str
        self.ui_effect_on(self.settings.get('EffectEnabled'), None)
        self.update_effect_controls()

    def update_effect_control(self, effect_control_key):
        info = self.effect_controls.get(effect_control_key)
        if info is None:
            log.error(f'Error in efect control info for key {effect_control_key}')
            return

        control_name = info.get('control_name')
        slider_id = info.get('slider_id')
        slider_id.disabled = True # The slider settings changed invoke the on_value call
        log.info(f'{control_name}')
        slider_id.min = self.midi_manager.cc_controls.get_min(control_name)
        log.info(f'{slider_id.min}')
        slider_id.max = self.midi_manager.cc_controls.get_max(control_name)
        value = self.settings.get(info.get('settings_name'))
        slider_id.value = value
        slider_id.disabled = False
        # effects can have text selections or numerical
        text_function = info.get('text_function')
        if text_function is not None:
            info.get('value_id').text = self.bold(text_function(value))
        else:
            info.get('value_id').text = self.bold(str(value))

        cc_str = self.midi_manager.cc_controls.get_cc_str(control_name)
        info.get('control_cc_id').text = cc_str
        self.midi_manager.cc_controls.register_ui_callback(control_name, self.ui_effect_control_update, control_name)


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


    def ui_effect_control_update(self, value, id_str):
        """
        update UI sliders to reflect CC changing the effect parm
        """
        log.info(f'ui_effect_control_update: {id_str}')
        info = self.effect_controls.get(id_str)
        if info is None:
            log.error(f'Unknown effects control name {id_str}')
            return

        slider_id = info.get('slider_id')
        slider_id.disabled = True
        slider_id.value = value
        slider_id.disabled = False

        text_getter = info.get('text_function')
        if text_getter is not None:
            text = self.bold(text_getter(value))
        else:
            text = self.bold(str(value))

        info.get('value_id').text = text
        
        

    def effect_control_update(self, value, id_str):
        """
        from the slider update text and effect
        """
        log.info(f'effect_control_update: {id_str}')
        info = self.effect_controls.get(id_str)
        if info is None:
            log.error(f'Unknown effects control name {id_str}')
            return

        value = int(value)
        text_getter = info.get('text_function')
        if text_getter is not None:
            text = self.bold(text_getter(value))
        else:
            text = self.bold(str(value))

        info.get('value_id').text = text

        if info.get('slider_id').disabled == False: # at startup when setting slider parms this call should not be made
            uf = info.get('update_function')
            if uf is not None:
                uf(value)


    def ui_effect_on(self, on, data):
        """
        called from either the ui or from a control
        """
        if on:
            self.ids.effect_on.state = 'down'
            self.ids.effect_off.state = 'normal'
        else:
            self.ids.effect_on.state = 'normal'
            self.ids.effect_off.state = 'down'

    def effect_on(self, on):
        self.ui_effect_on(on, None)
        self.effect_manager.effect_enable(on)

    def ui_control_map(self, ccbox):
        """
        called when UI CC box has a number
        remaps the UI number to this control
        """
        try:
            cc = int(ccbox.text)
        except:
            return

        if cc > MidiConstants().CC_MAX:
            ccbox.text = str(MidiConstants().CC_MAX)
            cc = MidiConstants().CC_MAX

        log.info(f'Mapping control CC: {cc} to {ccbox.name}')

        self.midi_manager.cc_controls.remap(ccbox.name, cc)

    def update_cc_box_learn(self, name, cc, ccbox):
        """
        when a control changes and we are in learn mode
        this is called back by midi in with the new cc and the box to update
        """
        log.info(f'ui - updating cc box {name} to cc: {cc}')
        try:
            cc = int(cc)
        except:
            return

        if cc > MidiConstants().CC_MAX:
           cc = MidiConstants().CC_MAX

        ccbox.text = str(cc)

    def control_cc_learn(self, ccbox, focus):
        """
        we learn when focused, set the cc control callback to learn
        This calls the remap, when defocused set the callback to process
        controls
        """
        log.info(f'focus: {ccbox.name}, {focus}')
        if focus:
            self.midi_manager.cc_controls.learn(ccbox.name, self.update_cc_box_learn, ccbox)
        else:
            self.midi_manager.cc_controls.unlearn()


    def error_notification(self, title='Error', msg='Something is wrong!'):
        #turns background red, popup is black kinda cool...
        popup = Popup(title=title, content=Label(markup=True,
                                                 text=self.bold(msg)),
                                                 size_hint=(None, None),
                                                 size=(300, 200),
                                                 background_color=(1, 0, 0, .7))
        popup.open()
        

    def update_port_selections(self):
        ports = self.midi_manager.get_midi_in_ports()
        if ports is not None:
            ports = ports.copy()
            ports.insert(0,'None') # we want to be able to close port too. 
            self.ids.midi_port_in.values = ports

        ports = self.midi_manager.get_midi_out_ports()
        if ports is not None:
            ports = ports.copy()
            ports.insert(0,'None')
            self.ids.midi_port_out.values = ports

    def update_clock_selections(self):
        """
        called once at startup
        """
        if self.midi_manager.clock_source == 'internal':
            self.ids.clock_internal.state = 'down'
            self.ids.clock_bpm_slider.disabled = False
        else:
            self.ids.clock_external.state = 'down'
            self.ids.clock_bpm_slider.disabled = True

        self.ids.clock_bpm_slider.min = self.midi_manager.cc_controls.get_min('InternalClockBPMControlCC')
        self.ids.clock_bpm_slider.max = self.midi_manager.cc_controls.get_max('InternalClockBPMControlCC')
        bpm = self.midi_manager.clock.get_bpm()
        if bpm < self.ids.clock_bpm_slider.min:
            bpm = self.ids.clock_bpm_slider.min

        self.ids.clock_bpm_slider.value = bpm
        self.midi_manager.cc_controls.register_ui_callback('InternalClockBPMControlCC', self.ui_change_internal_clock_bpm)
        cc_str = self.midi_manager.cc_controls.get_cc_str('InternalClockBPMControlCC')
        self.ids.InternalClockBPMControlCC.text = cc_str



    def ui_change_internal_clock_bpm(self, control, data):
        """
        changes slider if control changes
        """
        self.ids.clock_bpm_slider.disabled = True
        self.ids.clock_bpm_slider.value = self.midi_manager.clock.get_bpm()
        self.ids.clock_bpm_slider.disabled = False

    def change_internal_clock_bpm(self, value):
        """
        from slider changes clock bpm
        """
        if self.ids.clock_bpm_slider.disabled == True:
             return

        self.midi_manager.clock.change_bpm(int(value))

    def nav_button_pressed(self, but, screen_name):
        log.info(screen_name)
        but.state = 'down'
        self.ids['screen_manager'].current = screen_name
        self.settings.set('start_screen', screen_name)
        log.info(f'cwd: {os.getcwd()}')
        #Window.screenshot(name=f'{screen_name}' +'.png') # for website takes a snap of the screen

   
    def select_midi_input_port(self, selector):
        log.info(f'midi in port desired: {selector.text}') 
        if selector.text is 'None':
            self.midi_manager.close_midi_in_port()
            self.settings.set('midi_in_port', selector.text)
            return

        if self.midi_manager.set_midi_in_port(selector.text):
            self.settings.set('midi_in_port', selector.text)
            return

        self.error_notification(title='Error opening MIDI port', msg=f'{selector.text}')
        selector.text = selector.values[0]
        self.settings.set('midi_in_port', selector.text)
        log.error('error opening input port')

    def select_midi_output_port(self, selector):
        log.info(f'midi out port desired: {selector.text}') 
        if selector.text is 'None':
            self.midi_manager.close_midi_out_port()
            self.settings.set('midi_out_port', selector.text)
            return

        if self.midi_manager.set_midi_out_port(selector.text):
            self.settings.set('midi_out_port', selector.text)
            return

        self.error_notification(title='Error opening MIDI port', msg=f'{selector.text}')
        selector.text = selector.values[0]
        self.settings.set('midi_out_port', selector.text)
        log.error('error opening output port')

    def select_clock_source(self, but, internal_source):
        but.state = 'down'
        if internal_source:
            self.ids.clock_bpm_slider.disabled = False
            source = 'internal'
        else:
            self.ids.clock_bpm_slider.disabled = True
            source = 'external'

        self.effect.panic() # should do this in midi_manager, but it does not have effect. 

        self.midi_manager.set_clock_source(source)

        bpm = self.midi_manager.clock.get_bpm()
        if bpm != 0:
            self.clock_LED_event.timeout = 60.0/bpm



    def update_clock_LED(self, dt):
        if 'off' in self.ids.midi_clock_activity.source:
            self.ids.midi_clock_activity.source = 'media/red_led.png'
        else:
            self.ids.midi_clock_activity.source = 'media/off_led.png'

        bpm = self.midi_manager.clock.get_bpm()
        if bpm != 0:
            self.clock_LED_event.timeout = 60.0/bpm

        if self.ids.clock_bpm_slider.disabled == True:
            self.ids.clock_bpm_slider.value = self.midi_manager.clock.get_bpm() #external clock

        #self.midi_in_activity()

    def start_activity_LEDs(self):
        """
        The LEDS are toggled by a kivy clock interval or MIDI activity
        """
        bpm = self.midi_manager.clock.get_bpm()
        if bpm == 0:
            bpm = 1

        self.clock_LED_event = Clock.schedule_interval(self.update_clock_LED, 60.0/bpm)
        self.midi_manager.register_midiin_activity_callback(self.midi_in_activity)
        self.midi_manager.register_midiout_activity_callback(self.midi_out_activity)
        log.info('Started activity LEDs')

    def midi_in_activity(self):
        Clock.schedule_once(self.update_midi_in_LED)
        Clock.schedule_once(self.update_midi_in_LED, 0.2)

    def update_midi_in_LED(self, dt):
        if 'off' in self.ids.midi_in_activity.source:
            self.ids.midi_in_activity.source = 'media/red_led.png'
        else:
            self.ids.midi_in_activity.source = 'media/off_led.png'

    def midi_out_activity(self):
        Clock.schedule_once(self.update_midi_out_LED)
        Clock.schedule_once(self.update_midi_out_LED, 0.2)

    def update_midi_out_LED(self, dt):
         if 'off' in self.ids.midi_out_activity.source:
            self.ids.midi_out_activity.source = 'media/red_led.png'
         else:
            self.ids.midi_out_activity.source = 'media/off_led.png'

    def get_help_text(self):
        return help_text

    def license_entered(self, ti):
        """
        Verify entered values  
        """
        log.info(f'User email: {ti.text}')
        self.register_popup.dismiss()


    def registered(self):
        """
        if registered say so , else ask to register
        """
        return self.bold('REGISTER')


    def register(self):
        """
        here we accept the email and license key and activate the product
        WE are just asking for a email address no license or key etc. 
        """
        fl = FloatLayout()
        fl.add_widget(Label(
                            markup=True,
                            text=self.bold('ENTER EMAIL'),
                            size_hint=(None, None),
                            size=(300, 200),
                            pos_hint={'x':.05, 'center_y':.8}
                            ))

        input_email = TextInput(
                               # focus=True,
                                multiline=False,
                                size_hint=(None, None),
                                size=(300, 30),
                                pos_hint={'x':.05, 'center_y':.6}
                                )

        input_email.bind(on_text_validate=self.license_entered)

        fl.add_widget(input_email)

        popup = Popup(title='VIRTUAL ROBOT', 
                      content=fl,
                      size_hint=(None, None), 
                      size=(400, 200))

        popup.open()
        self.register_popup = popup


  
def save_settings(args):
    if gsettings is not None:
        gsettings.close()

    return False    # do not return True or window cannot be closed


class MainEchoApp(App):
    def build(self):
        self.title = 'Virtual Robot MIDI Echo'
          # Execute cleaning function when exiting app
        Window.bind(on_request_close=save_settings)
        return RootWidget() 

    

if __name__ == '__main__':
    MainEchoApp().run()
    log.info('exiting')
