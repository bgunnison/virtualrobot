import kivy
kivy.require('1.0.8')

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, RiseInTransition
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.graphics import Color, Rectangle
from kivy.properties import ListProperty
from kivy.utils import get_color_from_hex
from kivy.config import Config
Config.set('graphics', 'resizable', False)
Config.set('graphics', 'multisamples', 8)

Config.set('kivy','window_icon','media/icon.ico') # no work...

# maybe its cool?
# https://stackoverflow.com/questions/31179155/how-to-set-a-screen-background-image-in-kivy
#class RootScreen(ScreenManager):
#    pass

#class StartScreen(Screen):
#    pass
NAV_BUTTON_ON_COLOR = (1,1,1,1)  #kivy.utils.get_color_from_hex('#93FFFF')
NAV_BUTTON_OFF_COLOR = (1, 1, 1, .2)
NAV_BUTTON_TEXT_COLOR_OFF = '#d0d0d0'
NAV_BUTTON_TEXT_COLOR_ON = '#04d3ff'
NAV_BUTTON_TEXT_MARKUP_START_OFF = '[b][color=' + NAV_BUTTON_TEXT_COLOR_OFF + ']'
NAV_BUTTON_TEXT_MARKUP_START_ON = '[b][color=' + NAV_BUTTON_TEXT_COLOR_ON + ']'
NAV_BUTTON_TEXT_MARKUP_END = '[/color][/b]'

nav_button_ids = ['nav_midi', 'nav_echo', 'nav_live', 'nav_help']
screen_names = {'nav_midi':'screen_midi', 'nav_echo':'screen_echo', 'nav_live':'screen_live', 'nav_help':'screen_help'}

   

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



class RootWidget(BoxLayout):

    def __init__(self, **kwargs):
        super(RootWidget, self).__init__(**kwargs)

        # init nav buttons
        for id in nav_button_ids:
            self.ids[id].background_color = NAV_BUTTON_OFF_COLOR
            self.ids[id].text = NAV_BUTTON_TEXT_MARKUP_START_OFF + self.ids[id].text + NAV_BUTTON_TEXT_MARKUP_END

                            # pass button and button key
        self.nav_button_pressed(self.ids[nav_button_ids[0]], nav_button_ids[0])

    def nav_button_pressed(self, but, id_key):
        for id in nav_button_ids:
            self.ids[id].background_color = NAV_BUTTON_OFF_COLOR
            self.ids[id].text = self.ids[id].text.replace(NAV_BUTTON_TEXT_COLOR_ON, NAV_BUTTON_TEXT_COLOR_OFF)

        but.background_color = NAV_BUTTON_ON_COLOR
        but.text = but.text.replace(NAV_BUTTON_TEXT_COLOR_OFF, NAV_BUTTON_TEXT_COLOR_ON)
        
        print(id_key)

        self.ids['screen_manager'].current = screen_names[id_key]
   


class MainEchoApp(App):
    def build(self):
        self.title = 'Virtual Robot MIDI Echo'
        
        return RootWidget() 

    

if __name__ == '__main__':
    MainEchoApp().run()
