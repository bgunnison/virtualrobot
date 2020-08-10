"""
 Copyright (C) 2020 Brian R. Gunnison
 
 This file is part of MIDI EFFECTS project

 This is the main class for all MIDI EFFECTS
 
 This file can not be copied and/or distributed without the express
 permission of Brian R. Gunnison
"""
import sys
import os
import time
import logging
from pathlib import Path


help_text = '' 


logging.basicConfig(level=logging.ERROR)
log = logging.getLogger(__name__)

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from midiapps.midi_effect_manager import MidiEffectManager
from common.midi import MidiManager, MidiConstants
from common.upper_class_utils import Settings

import kivy
kivy.require('1.11.1')

from kivy.config import Config
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')
Config.set('graphics', 'resizable', False)
Config.set('graphics', 'multisamples', 8)


from kivy.app import App
from kivy.core.window import Window
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
from kivy.clock import Clock
from kivy.factory import Factory
from kivy.properties import ObjectProperty

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

class EffectScreen(Screen):
    pass

class HelpScreen(Screen):
    pass

class SaveScreen(Screen):
    pass

class LoadScreen(Screen):
    pass

class CCControlInput(TextInput):
    pass


class ScrollableLabel(ScrollView):
    pass




    
class RootWidget(BoxLayout):

    def __init__(self, title='generic', effect=None, use_clock=True, **kwargs):
        super(RootWidget, self).__init__(**kwargs)
        self.use_clock=use_clock # some apps don't need a MIDI clock

        #self.loadfile = ObjectProperty(None)
        #self.savefile = ObjectProperty(None)

        self.start_app(title, effect)

    def start_app(self, title, effect):
        """
        global_settings are global to the app, config_settings are the saved configuration
        """
        self.global_settings = Settings(title, type='global')    #global settings calls to set will save the file

        #registration does nothing but store what was entered
        self.ids.RegisteredUserBut.text = self.bold(self.global_settings.get('registered_user', 'REGISTER'))
        self.register_popup_text_box = None
        self.register_popup = None

        self.current_settings = Settings(title) 
        path = self.global_settings.get('ConfigPath', '/')
        file = self.global_settings.get('ConfigFile', '')
        if self.current_settings.set_path(path, file) == False:
            # something may have happened to the file
            self.global_settings.set('ConfigPath', '/')
            self.global_settings.set('ConfigFile', '')
            

        self.midi_manager = MidiManager(self.current_settings, use_clock=self.use_clock)
        self.effect = effect(self.current_settings, self.midi_manager.cc_controls)
        self.effect_manager = MidiEffectManager(self.current_settings, self.effect, self.midi_manager)

        self.effect_controls = {} # dict keyd by effect control name with ui ids to update if we get a CC control

        # restore screen from settings
        but = None
        screen = self.global_settings.get('start_screen', 'screen_help') # first screen at install is help
        if 'midi' in screen:
            but = self.ids.nav_midi
        if 'effect' in screen:
            but = self.ids.nav_effect
        if 'help' in screen:
            but = self.ids.nav_help
        if 'save' in screen:
            but = self.ids.nav_save
        if 'load' in screen:
            but = self.ids.nav_load
        if but is None:
            but = self.ids.nav_midi
            screen = 'screen_midi'

        self.nav_button_pressed(but, screen)

        self.update_midi_screen()

        self.update_effect_screen()

        # call last
        self.effect_manager.run()

        self.start_activity_LEDs()

    def bold(self, text):
        return '[b]' + text + '[/b]' # markup must be true, this is our style plus CAPS

    def destroy(self):
        """
        call when exiting app
        """
        self.effect.panic()
        self.midi_manager.destroy()
        self.global_settings.close()
        log.info('destroy finished')

    def set_file_chooser_path(self, chooser_name):
        """
        sets file chooser screen path
        """
        if chooser_name == 'load':
            set_name = 'LoadFileChooserPath'
            chooser = self.ids.load_filechooser

        if chooser_name == 'save':
            set_name = 'SaveFileChooserPath'
            chooser = self.ids.save_filechooser


        path = self.global_settings.get(set_name, '/')
        try:
            p = Path(path)
            if p.exists() == False:
                self.global_settings.set(set_name, '/')
                p = '/' # default to root if any errors
        except:
            p = '/'

        chooser.path = str(p)

    #def file_chooser_on_entry_added(self, file_chooser, file_list_entry):
    #    log.info(f'entry_added: {entry}, {parent}')
    #def file_chooser_on_subentry_to_entry(self, entry, parent):
    #    log.info(f'subentry_to_entry: {entry}, {parent}')


    def save_file_chooser_on_entries_cleared(self, chooser):
        # fires off when chooser view changes
        # remember path so we can restore it when screen loads
        log.info(f'save on_entries_cleared, path: {chooser.path}')
        self.global_settings.set('SaveFileChooserPath', chooser.path)
        self.ids.save_settings_text_input.text = chooser.path

    def load_file_chooser_on_entries_cleared(self, chooser):
        # fires off when chooser view changes
        # remember path so we can restore it when screen loads
        log.info(f'load on_entries_cleared, path: {chooser.path}')
        self.global_settings.set('LoadFileChooserPath', chooser.path)
        self.ids.load_settings_text_input.text = chooser.path


    def load_settings(self, path, filenames):
        filename = filenames[0]
        log.info(f'load settings: {path}, {filename}')
        if self.current_settings.set_path(path, filename, must_exist=True) == False:
            self.error_notification(title='Cannot load!', msg=f'{path}, {filename}')
            return

        if self.current_settings.load() == False:
            err = self.current_settings.get_last_error()
            self.error_notification(title='Cannot load!', msg=f'{path}, {filename}, {err}')
            return

        
    def save_settings(self, path, filename):
        log.info(f'save settings: {path}, {filename}')
        if self.current_settings.set_path(path, filename) == False:
            err = self.current_settings.get_last_error()
            self.error_notification(title='Error - cannot save!', msg=f'{path}, {filename}, {err}')
            return

        if self.current_settings.save() == False:
            err = self.current_settings.get_last_error()
            self.error_notification(title='Cannot save!', msg=f'{path}, {filename}, {err}')
            return

        self.global_settings.set('ConfigPath', path)
        self.global_settings.set('ConfigFile', filename)

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
        midi_port = self.current_settings.get('midi_in_port')
        if midi_port is not None:
            ports = self.midi_manager.get_midi_in_ports()
            if ports is not None:
                if midi_port in ports:
                    self.ids.midi_port_in.text = midi_port # fires off select_midi_input_port
                    #self.select_midi_input_port(self.ids.midi_port_in)

        midi_port = self.current_settings.get('midi_out_port')
        if midi_port is not None:
            ports = self.midi_manager.get_midi_out_ports()
            if ports is not None:
                if midi_port in ports:
                    self.ids.midi_port_out.text = midi_port # fires off select_midi_input_port
                    #self.select_midi_output_port(self.ids.midi_port_out)


    def update_effect_screen(self):
        self.midi_manager.cc_controls.register_ui_callback('EffectEnableControlCC', self.ui_effect_on)
        cc_str = self.midi_manager.cc_controls.get_cc_str('EffectEnableControlCC')
        self.ids.EffectEnableControlCC.text = cc_str
        self.ui_effect_on(self.current_settings.get('EffectEnabled'), None)
        self.update_effect_controls()

    def update_effect_control(self, effect_control_key):
        info = self.effect_controls.get(effect_control_key)
        if info is None:
            log.error(f'Error in efect control info for key {effect_control_key}')
            return

        control_name = info.get('control_name')
        slider_id = info.get('slider_id')
        slider_id.disabled = True # The slider settings changed invoke the on_value call
        #log.info(f'{control_name}')
        slider_id.min = self.midi_manager.cc_controls.get_min(control_name)
        #log.info(f'{slider_id.min}')
        slider_id.max = self.midi_manager.cc_controls.get_max(control_name)
        settings_name = info.get('settings_name')
        if 'XObject' in settings_name:
             # get the current settings object number
            settings_name = settings_name.replace('XObject',f'{self.effect.get_settings_xobject()}')

        value = self.current_settings.get(settings_name)
           
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


    def nav_button_pressed(self, but, screen_name):

        # set the path for the choosers
        if 'load' in screen_name:
           self.set_file_chooser_path('load')
        if 'save' in screen_name:
            self.set_file_chooser_path('save')

        log.info(screen_name)
        but.state = 'down'
        self.ids['screen_manager'].current = screen_name
        self.global_settings.set('start_screen', screen_name)
       # log.info(f'cwd: {os.getcwd()}')
        #Window.screenshot(name=f'{screen_name}' +'.png') # for website takes a snap of the screen


    def ui_effect_control_update(self, value, id_str):
        """
        update UI sliders to reflect CC changing the effect parm
        """
       # log.info(f'ui_effect_control_update: {id_str}')
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
        #log.info(f'effect_control_update: {id_str}')
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

        if self.midi_manager.cc_controls.remap(ccbox.name, cc) == False:
            # can't duplicate a CC map
            cc = self.midi_manager.cc_controls.get_cc(ccbox.name)
            ccbox.text = str(cc)

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
                                                 size=(500, 200),
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
        if self.use_clock == False:
            return

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


   
    def select_midi_input_port(self, selector):
        log.info(f'midi in port desired: {selector.text}') 
        if selector.text is 'None':
            self.midi_manager.close_midi_in_port()
            self.current_settings.set('midi_in_port', selector.text)
            return

        if self.midi_manager.set_midi_in_port(selector.text):
            self.current_settings.set('midi_in_port', selector.text)
            return

        self.error_notification(title='Error opening MIDI port', msg=f'{selector.text}')
        selector.text = selector.values[0]
        self.current_settings.set('midi_in_port', selector.text)
        log.error('error opening input port')

    def select_midi_output_port(self, selector):
        log.info(f'midi out port desired: {selector.text}') 
        if selector.text is 'None':
            self.midi_manager.close_midi_out_port()
            self.current_settings.set('midi_out_port', selector.text)
            return

        if self.midi_manager.set_midi_out_port(selector.text):
            self.current_settings.set('midi_out_port', selector.text)
            return

        self.error_notification(title='Error opening MIDI port', msg=f'{selector.text}')
        selector.text = selector.values[0]
        self.current_settings.set('midi_out_port', selector.text)
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
        if bpm < self.ids.clock_bpm_slider.min:
            bpm = self.ids.clock_bpm_slider.min

        self.ids.clock_bpm_slider.value = bpm
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
        if self.use_clock == True:
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
        return ''

    def set_license(self, text):
        """
        Verify entered values  
        """
        if text == '':
            text = 'REGISTER'

        log.info(f'User email: {text}')
        self.global_settings.set('registered_user', text)
        self.register_popup.dismiss()
        self.ids.RegisteredUserBut.text = self.bold(text)
        self.register_popup_text_box = None
        self.register_popup = None

    def license_entered(self, ti):
        """
        return hit in text box  
        """
        self.set_license(ti.text)
        

    def license_pressed(self, but):
        """
        Verify entered values  
        """
        
        self.set_license(self.register_popup_text_box.text)
        

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
                            pos_hint={'center_x':.5, 'center_y':.8}
                            ))

        input_email = TextInput(
                               # focus=True,
                                id='licenseTextBox', 
                                multiline=False,
                                size_hint=(None, None),
                                size=(300, 30),
                                pos_hint={'center_x':.5, 'center_y':.6}
                                )

        input_email.bind(on_text_validate=self.license_entered)

        fl.add_widget(input_email)
        self.register_popup_text_box = input_email

        input_email_but = Button(
                                markup=True,
                                text=self.bold('DONE'),
                                size_hint=(None, None),
                                size=(60, 30),
                                pos_hint={'center_x':.5, 'center_y':.3}
                                )

        input_email_but.bind(on_press=self.license_pressed)

        fl.add_widget(input_email_but)

        popup = Popup(title='VIRTUAL ROBOT', 
                      content=fl,
                      size_hint=(None, None), 
                      size=(400, 200))

        popup.open()
        self.register_popup = popup


 
