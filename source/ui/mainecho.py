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
    def insert_text(self, substring, from_undo=False):
        try:
            v = int(substring)
        except:
            return

        return super(CCControlInput, self).insert_text(substring, from_undo=from_undo)


class RootWidget(BoxLayout):

    def __init__(self, **kwargs):
        super(RootWidget, self).__init__(**kwargs)

        self.midi_manager = MidiManager()
        self.effect = MidiEchoEffect()
        self.effect_manager = MidiEffectManager(self.effect, self.midi_manager)

        self.nav_button_pressed('screen_midi')

        self.update_midi_screen()

        self.update_echo_screen()

        self.effect_manager.run()

        self.start_activity_LEDs()


    def update_midi_screen(self):
        self.update_port_selections()
        self.update_clock_selections()

    def update_echo_screen(self):
        self.effect_manager.register_cc_callback('Enable', self.effect_on)


    def effect_on(self, on):
        if on:
            self.ids.effect_on.state = 'down'
            self.ids.effect_off.state = 'normal'
        else:
            self.ids.effect_on.state = 'normal'
            self.ids.effect_off.state = 'down'

        self.effect_manager.effect_enable(on)


    def cc_control_map_effect_enable(self, input):
        log.info(f'Effect enable control CC: {input.text}')
        try:
            cc = int(input.text)
        except:
            return

        if cc > MidiConstants().CC_MAX:
            input.text = str(MidiConstants().CC_MAX)
            cc = MidiConstants().CC_MAX

        self.effect_manager.remap_cc('Enable', cc)

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
        if self.midi_manager.internal_clock:
            self.ids.clock_internal.state = 'down'
            self.ids.clock_bpm_slider.value = self.midi_manager.clock_source.get_bpm()
        else:
            self.ids.clock_external.state = 'down'

    def change_internal_clock_bpm(self, value):
        #log.info(f'internal clock bpm: {int(value)}')
        self.midi_manager.change_clock_bpm(int(value))

    def nav_button_pressed(self, screen_name):
        log.info(screen_name)

        self.ids['screen_manager'].current = screen_name
   
    def select_midi_input_port(self, selector):
        log.info(f'midi in port desired: {selector.text}') 
        if selector.text is 'None':
            self.midi_manager.close_midi_in_port()
            return

        if self.midi_manager.set_midi_in_port(selector.text):
            return

        self.error_notification(title='Error opening MIDI port', msg=f'{selector.text}')
        selector.text = selector.values[0]
        log.error('error opening input port')

    def select_midi_output_port(self, selector):
        log.info(f'midi out port desired: {selector.text}') 
        if selector.text is 'None':
            self.midi_manager.close_midi_out_port()
            return

        if self.midi_manager.set_midi_out_port(selector.text):
            return

        self.error_notification(title='Error opening MIDI port', msg=f'{selector.text}')
        selector.text = selector.values[0]
        log.error('error opening output port')

    def select_external_clock(self, but):
        log.error('wip')
        #log.info(f'Using external clock from MIDI port: "{self.ids.midi_port_in.text}"')

    def select_internal_clock(self, but):
        log.error('wip')
        #print(f'Sending clock out MIDI port: "{self.ids.midi_port_out.text}"')

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
