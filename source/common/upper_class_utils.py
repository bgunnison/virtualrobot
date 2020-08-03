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
#import shelve
from datetime import datetime
#import rsa
import json

logging.basicConfig(level=logging.ERROR)
log = logging.getLogger(__name__)

"""
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
"""

class Settings:
    """
    persistant storage
    """
    def __init__(self, app_name='generic', path=None):
        """
        Try to make this foolproof...
        put global settings in user dir 
        use a json file for settings
        """
        self.last_error = None
        self.path = None # a Path object
        if path is None: # this is the global settings
            if self.global_settings(app_name) == False:
                return
        else:
            try:
                p = Path(path)
            except:
                self.set_last_error(f'Error in settings path: {path}')
                return

            if p.is_file(path) == False:
                self.set_last_error(f'Error settings path: {path} does not exist')
                return

            self.path = p


        log.info(f'Path: {self.path}')
        self.settings = {}

        self.load()  
        self.dump() 

        self.set('App', app_name)

        if self.settings.get('Created') is None:
            now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            log.info(f'Settings at {self.path} created at: {now}')
            self.set('Created', now)

        self.set('Path', str(self.path))
        self.save()

    def get_last_error(self):
        return self.last_error  # returns None if all OK

    def set_last_error(self, error):
        self.last_error = error
        log.error(error)


    def global_settings(self, app_name):
        path = os.path.expanduser(os.path.join('~', 'AppData', 'Local', 'VIRTUALROBOT', app_name))
        p = Path(path)
        if p.exists() == False:
            log.info(f'Creating global settings path: {self.path}')
            try:
                p.mkdir(parents=True)
            except:
                self.set_last_error( f'Cannot create global settings path {self.path}')
                return False

        self.path = Path.joinpath(p, 'global.cfg')
        return True

    def load(self):
        """
        Gave up on using shelve as its not good for managing one file
        """
        if self.path.exists():
            try:
                with self.path.open() as json_file:
                    self.settings = json.load(json_file)
            except:
                self.set_last_error( f'Error opening settings at: {self.path}')
        else:
            log.info('File {self.path} does not esits yet')

    def save(self):
        try:
            with self.path.open('w') as outfile:
                json.dump(self.settings, outfile, indent=4, ensure_ascii=True)
        except:
            self.set_last_error(f'Error saving settings, path: {self.path}')

    def set(self, name, value):
        if isinstance(name, str) == False:
            self.set_last_error(f'Set name must be a string, got: {name}')
            return False

        try:
            self.settings[name] = value
        except:
            self.set_last_error(f'Error setting: {name} to {value}')
            return False

        log.info(f'Settings set: {self.path}, {name}, {value}')

        return True

    def get(self, name, default_value=None):
        """
        if not in settings, set default value
        """
        if isinstance(name, str) == False:
            self.set_last_error(f'Get name must be a string, got: {name}')
            return None

        value = self.settings.get(name)
        if value is None and default_value is not None:
            log.info(f'Setting default: {name} to {default_value}')
            self.set(name, default_value)
            return default_value

        log.info(f'Get: {name}: {value}')
        return value

    def dump(self):
        try:
            for k in self.settings.keys():
                v = self.settings[k]
                log.info(f'Stored setting: {k}, {v}')
        except:
            self.set_last_error( f'Settings dump encountered an error, key: {k}')
            return False # a bad config file

        return True


    def close(self):

        self.debug_log('Closing')
        self.dump()
        self.save()

        log.info(f'Settings closed {self.path}')

    def __del__(self):
        log.info('Deleting')
        self.close()
        





class NoteManager:
    """
    A simple priority queue of note events
    These are added at clock tick priority and examined 
    if it is their time to be sent out
    """

    def __init__(self):
        self.note_events = queue.PriorityQueue()
        self.midiout = None

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

        self.midiout = midiout

    def add(self, tick, message):
        """
        Add a message to the priority queue
        """
        self.note_events.put((tick, message))
        #log.info(f"Add: {message}, {tick}")

    def purge(self):
        self.note_events = None
        self.note_events = queue.PriorityQueue()

    def panic(self):
        self.note_events = None
        self.note_events = queue.PriorityQueue()

    def is_empty(self):
        return self.note_events.empty()

