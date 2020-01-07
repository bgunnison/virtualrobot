import kivy
kivy.require('1.0.8')

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.label import Label
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.graphics import Color, Rectangle

# maybe its cool?
# https://stackoverflow.com/questions/31179155/how-to-set-a-screen-background-image-in-kivy
#class RootScreen(ScreenManager):
#    pass

#class StartScreen(Screen):
#    pass

class RootWidget(FloatLayout):
    pass


class TitleBoxLayout(BoxLayout):
    pass

class LogoZipped(BoxLayout):
    pass

class MainEchoApp(App):
    def build(self):
        g = RootWidget() # RootScreen() #
        title_box = TitleBoxLayout()
        #title_box.add_widget(LogoZipped())
        g.add_widget(title_box)
        return g



if __name__ == '__main__':
    MainEchoApp().run()
