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

from midiapps.midi_echo import MidiEchoEffect
from midiapps.midi_effect_manager import MidiEffectManager
from common.midi import MidiManager, MidiConstants
from common.upper_class_utils import Settings

import kivy
kivy.require('1.0.8')

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, RiseInTransition
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.graphics import Color, Rectangle
from kivy.uix.spinner import Spinner
from kivy.uix.slider import Slider
from kivy.uix.popup import Popup
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.config import Config
Config.set('graphics', 'resizable', False)
Config.set('graphics', 'multisamples', 8)

#Config.set('kivy','window_icon','media/icon.ico') # no work...

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
    

class RootWidget(BoxLayout):

    def __init__(self, **kwargs):
        super(RootWidget, self).__init__(**kwargs)

        self.settings = Settings('MidiEcho')    # our persistant settings

        self.midi_manager = MidiManager(self.settings)
        self.effect = MidiEchoEffect(self.settings)
        self.effect_manager = MidiEffectManager(self.settings, self.effect, self.midi_manager)

        # restore screen in settings
        screen = self.settings.get('start_screen', 'screen_midi')
        if 'midi' in screen:
            but = self.ids.nav_midi
        if 'echo' in screen:
            but = self.ids.nav_echo
        if 'live' in screen:
            but = self.ids.nav_live
        if 'help' in screen:
            but = self.ids.nav_help

        self.nav_button_pressed(but, screen)

        self.update_midi_screen()

        self.update_echo_screen()

        # call last
        self.effect_manager.run()

        self.start_activity_LEDs()


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

    def ui_effect_on(self, on):
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
        self.ui_effect_on(on)
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



    def error_notification(self, title='Error', msg='Something is wrong!'):
        #turns background red, popup is black kinda cool...
        popup = Popup(title=title, content=Label(markup=True,
                                                 text='[b]' + msg + '[/b]'),
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
        if self.midi_manager.internal_clock:
            self.ids.clock_internal.state = 'down'
            self.ids.clock_bpm_slider.disabled = False
            self.ids.clock_bpm_slider.min = self.midi_manager.clock_source.get_min_max()[0]
            self.ids.clock_bpm_slider.max = self.midi_manager.clock_source.get_min_max()[1]
            self.ids.clock_bpm_slider.value = self.midi_manager.clock_source.get_bpm()
            self.midi_manager.cc_controls.register_ui_callback('InternalClockBPMControlCC', self.ui_change_internal_clock_bpm)
            cc_str = self.midi_manager.cc_controls.get_cc_str('InternalClockBPMControlCC')
            self.ids.InternalClockBPMControlCC.text = cc_str

        else:
            self.ids.clock_external.state = 'down'
            self.ids.clock_bpm_slider.disabled = True


    def ui_change_internal_clock_bpm(self, control):
        """
        changes slider if control changes
        """
        self.ids.clock_bpm_slider.value = self.midi_manager.clock_source.get_bpm()

    def change_internal_clock_bpm(self, value):
        """
        from slider changes clock bpm
        """
        self.midi_manager.clock_source.change_bpm(int(value))

    def nav_button_pressed(self, but, screen_name):
        log.info(screen_name)
        but.state = 'down'
        self.ids['screen_manager'].current = screen_name
        self.settings.set('start_screen', screen_name)
   
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
            self.midi_manager.set_clock_source(internal=True)
        else:
            self.ids.clock_bpm_slider.disabled = True


    def update_clock_LED(self, dt):
        if 'off' in self.ids.midi_clock_activity.source:
            self.ids.midi_clock_activity.source = 'media/red_led.png'
        else:
            self.ids.midi_clock_activity.source = 'media/off_led.png'

        bpm = self.midi_manager.clock_source.get_bpm()
        self.clock_LED_event.timeout = 60.0/bpm

        #self.midi_in_activity()

    def start_activity_LEDs(self):
        """
        The LEDS are toggled by a kivy clock interval or MIDI activity
        """
        bpm = self.midi_manager.clock_source.get_bpm()
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

       

class MainEchoApp(App):
    def build(self):
        self.title = 'Virtual Robot MIDI Echo'
        
        return RootWidget() 

    

if __name__ == '__main__':
    MainEchoApp().run()
    time.sleep(10)
