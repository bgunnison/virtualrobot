"""
 Copyright (C) 2020 Brian R. Gunnison
 
 This file is part of MIDI EFFECTS project
 
 MIDI EFFECTS can not be copied and/or distributed without the express
 permission of Brian R. Gunnison
"""
import os
import sys
import logging

logging.basicConfig(level=logging.ERROR)
log = logging.getLogger(__name__)

from common.midi import MidiNoteMessage, MidiConstants



class Effect:
    """
    Things common to midi effects
    """
    def __init__(self, settings, cc_controls=None):
        self.settings = settings
        self.name = 'MIDI Effect'
        self.cc_controls = cc_controls
        self.note_manager = None
        # this for purge, any effect that creates notes adds them here.
        # purge will send their note offs. Typically used for turning effect off in the middle
        self.note_on_events = set([])

    def add_note_on_event(self, message):
        # keep a set of note on events pending, if the effect is turened off we can purge them
        # if a note off event we remove the note from the set
        #log.info(f'add_note_on_event msg: {message}')
        
        try:
            note = MidiNoteMessage(message)
        except:
            log.debug('add_note_on_event message error')
            return

        if note.is_note_off():
            note.make_note_on() # notes are stored as on
            event = (note.type_channel, note.note)
            #log.info(f'note off event: {event}')
            if event in self.note_on_events:
               # log.info(f'note off remove event: {event}')
                self.note_on_events.remove(event)
            return

        # events are unique by note and channel
        event = (note.type_channel, note.note)

        #log.info(f'note on add event: {event}')
        self.note_on_events.add(event)

    def purge(self, midiout):
        if midiout is None:
            self.note_on_events.clear()
            return

        try:
            # saw an exception where someone was modifying this set whilst iterating over it below. 
            purge_events = self.note_on_events.copy()
            self.note_on_events.clear()
        except:
            log.debug('exception copying purge events')
            return


        for event in purge_events:
            message = [event[0], event[1], 0]
            note = MidiNoteMessage(message)
            note.make_note_off()
            #log.info(f'Purging: {message} ')
            midiout.send_message(message)

        #log.info('Purge finished')
        purge_events.clear()


    def get_name(self):
        return self.name

    def enable(self):
        pass # override, called when effect on button is pressed

    def disable(self):
        pass # ovveride called when effect off button is pressed

    def run(self):
        pass # override


class MidiEffectManager:

    def __init__(self, settings, effect, midi_manager):
        self.settings = settings
        self.midi_manager = midi_manager      
        self.effect = effect
        self.effect_enable(self.settings.get('EffectEnabled', False))
        # button CCs are mapped to to enable (for example) the effect
        self.midi_manager.cc_controls.add(name='EffectEnableControlCC', cc_default=48, type='switch', control_callback=self.effect_enable)

    def effect_enable(self, on):
        log.info(f'Effect: {self.effect.get_name()} is {on}')
        self.effect_enabled = on
        if self.effect_enabled == False:
            self.effect.disable()
            self.effect.purge(self.midi_manager.midiout) # get rid of any hanging notes
            self.midi_manager.midiout.purge()
        else:
            self.effect.enable()

        self.settings.set('EffectEnabled', on)


    def run(self):
        self.midi_manager.register_note_callback(self.note_callback)
        self.midi_manager.register_clock_callback(self.clock_callback)
        self.midi_manager.midiin.run()
        log.info('Running')

    def apply_effect(self, tick, message):
        """
        A effect object acts on the incoming note
        and may add note events to the note manager to play in the future
        """
        if self.effect_enabled == False:
            self.midi_manager.midiout.send_message(message)  # send original note event
            return

        self.effect.run(tick, self.midi_manager.midiout, message)


    def note_callback(self, message, clock_source):
        """
        invoked by our input when a note is on or off
        """ 
        tick = 0
        if clock_source is not None:
            tick = clock_source.get_tick()
        #log.info(f"Note callback: {message}, {tick}")
        self.apply_effect(tick, message)         # may add  note events for the future
        if self.effect.note_manager is not None:
            self.effect.note_manager.run(tick, self.midi_manager.midiout)        


    def clock_callback(self, tick, data):
        """
        called at midi clock intervals or at 60 bpm every 42 msec - 24 times per quarter note
        here we run the note manager and it sends or stops notes as queued
        This runs quite fast so no delays...
        """
        #log.info(f"Clock callback: {tick}")
        self.effect.note_manager.run(tick, self.midi_manager.midiout)
    
