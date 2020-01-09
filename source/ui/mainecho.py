import kivy
kivy.require('1.0.8')

from kivy.app import App
#from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.label import Label
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.bubble import Bubble
from kivy.uix.button import Button
from kivy.graphics import Color, Rectangle
from kivy.properties import ListProperty
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
NAV_BUTTON_ON_COLOR = (0.1, 0.1, .2, 1.0)
NAV_BUTTON_OFF_COLOR = (0, 0, 0, .8)
nav_button_ids = ['nav_midi', 'nav_echo', 'nav_live', 'nav_help']

class RootWidget(BoxLayout):
    

    def __init__(self, **kwargs):
        super(RootWidget, self).__init__(**kwargs)

    def nav_button_pressed(self, but, id_key):
        for id in nav_button_ids:
            self.ids[id].background_color = NAV_BUTTON_OFF_COLOR

        but.background_color = NAV_BUTTON_ON_COLOR
        #print(self.ids.keys())
        print(id_key)
   
    


class TitleBoxLayout(BoxLayout):
    pass

class NavButtons(BoxLayout):
    pass


class LogoZipped(BoxLayout):
    pass

class MainEchoApp(App):
    def build(self):
        self.title = 'Virtual Robot MIDI Echo'
        
        return RootWidget() 

    

if __name__ == '__main__':
    MainEchoApp().run()
