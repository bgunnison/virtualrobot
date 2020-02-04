"""
 Copyright (C) 2020 Brian R. Gunnison
 
 This file is part of MIDI project
 
 MIDI can not be copied and/or distributed without the express
 permission of Brian R. Gunnison
"""
import os
import glob
import queue
import logging
from pathlib import Path
import shelve
from datetime import datetime
import rsa

logging.basicConfig(level=logging.ERROR)
log = logging.getLogger(__name__)

class license:
    def __init__(self, email, signature):

        self.valid = False
        pubkey = ''
        try:
            rsa.verify(email.encode('utf-8'), signature, pubkey)
        except rsa.VerificationError:
            log.error(f'Invalid key: {email}')
            return

        log.info(f'Valid key: {email}')
        self.valid = True

    def is_valid(self):
        return self.valid

class Settings:
    """
    persistant storage
    """
    def __init__(self, app_name='generic'):
        """
        Try to make this foolproof...
        put settings in user dir in case other dirs are admin
        we create the path dirs
        then create the shelve files, if these fail we resort to a dictionay so set and get work, but persistance fails
        todo: multiple apps of same type?
        """
        self.path = os.path.expanduser(os.path.join('~', 'VirtualRobot', app_name))
        self.settings = None
        self.persist = True

        self._open()        

        now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        #log.info(f'Settings at {self.path} started: {now}')
        self.set(app_name, now)
        self.set('path', self.path)
        self.dump()

        self.save()
     
    def _open(self, start_over=False):
        if start_over:
            thispath = os.path.join(self.path, '*')
            files = glob.glob(thispath)
            for file in files:
                if 'config' in file:
                    os.remove(file)


        # flag = 'n'  # NOT ON WINDOWS!! Always create a new, empty database, open for reading and writing

        try:
            Path(self.path).mkdir(parents=True, exist_ok=True)
            pathfile = os.path.expanduser(os.path.join(self.path, 'config'))
            self.settings = shelve.open(pathfile, writeback=False)
            self.persist = True
        except:
            str = f'Error opening settings at: {self.path}'
            log.error(str)
            self.settings = {}  # use a dict so all the calls don't fail and we can get settings
            self.persist = False

    def save(self):
        if self.persist:
            self.settings.sync()

    def set(self, name, value):
        self.settings[name] = value
        log.info(f'Settings set: {self.path}, {name}, {value}')

    def get(self, name, default_value=None):
        """
        if not in settings, set default value
        """
        try:
            value = self.settings[name]
        except:
            self.set(name, default_value)
            return default_value

        return value

    def dump(self):
        try:
            for k, v in self.settings.items():
                log.info(f'Setting: {k}, {v}')
        except:
            self.settings.close()
            self._open(start_over=True)

    def close(self):
        self.dump()
        if self.persist:
            self.settings.close()
        log.info(f'Settings closed {self.path}')

    def __del__(self):
        self.close()
        



class Effect:
    """
    Things common to midi effects
    """
    def __init__(self, settings, cc_controls=None):
        self.settings = settings
        self.name = 'MIDI Effect'
        self.cc_controls = cc_controls


    def get_name(self):
        return self.name

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
        if self.note_events is None:
            return

        if self.note_events.empty():
            return

        # no peek ;(
        event = self.note_events.get()

        if tick >= event[0]:
            #log.info(f"Run: {tick}")
            midiout.send_message(event[1])
        else:
            self.note_events.put(event)

    def add(self, tick, message):
        """
        Add a message to the priority queue
        """
        self.note_events.put((tick,message))
        #log.info(f"Add: {message}, {tick}")

    def panic(self):
        self.note_events = None
        self.note_events = queue.PriorityQueue()

    def empty(self):
        return self.note_events.empty()

