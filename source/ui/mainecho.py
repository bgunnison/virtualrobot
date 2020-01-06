import kivy
kivy.require('1.0.8')

from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label


class EchoApp(App):
    def build(self):
        g = GridLayout()
        title = Label(text='Virtual Robot', font_size=120)
        g.add_widget(title)
        return g



if __name__ == '__main__':
    EchoApp().run()
