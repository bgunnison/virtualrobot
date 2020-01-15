"""
 Copyright (C) 2020 Brian R. Gunnison
 
 This file is part of MIDI project
 
 MIDI can not be copied and/or distributed without the express
 permission of Brian R. Gunnison
"""
import queue
import logging


logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

class Effect:
    """
    Things common to midi effects
    """
    def __init__(self):
        self.name = 'MIDI Effect'
        self.control_map = {}

    def get_name(self):
        return self.name

    def control_to_selection(self, selections, control):
        """
        a cc value is mapped to a range of selections in a list
        """
        n = len(selections)
        s = 128/n
        t = int(control/s)
        if t > n - 1:
            t = n - 1

        return t

    def run(self):
        pass # override



class NoteManager:
    """
    A simple priority queue of note events
    These are added at clock tick priority and examined 
    if it is their time to be sent out
    """

    def __init__(self):
        self.note_events = queue.PriorityQueue()

    def run(self, tick, midiout):
        """
        See if any events are ready to play
        """
        if self.note_events.empty():
            return

        # no peek ;(
        event = self.note_events.get()

        if tick >= event[0]:
            log.info(f"Run: {tick}")
            midiout.send_message(event[1])
        else:
            self.note_events.put(event)

    def add(self, tick, message):
        """
        Add a message to the priority queue
        """
        self.note_events.put((tick,message))
        log.info(f"Add: {message}, {tick}")

    def empty(self):
        return self.note_events.empty()

