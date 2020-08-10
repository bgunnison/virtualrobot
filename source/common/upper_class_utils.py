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
    def __init__(self, app_name='generic', type='empty'):
        """
        Try to make this foolproof...
        put global settings in user dir 
        use a json file for settings
        if type is None we create an empty settings, use set_path then save to save settings.
        if type is 'global' we create a settings file in user dir and save every time set is called
        if path and file are set we save to that. 
        """
        self.app_name = app_name # setting files must have this to be valid
        self.dirty = False #if true we save on every call to set 
        self.last_error = None
        self.path = None # a Path object
        self.settings = {}

        if type == 'global': # this is the global settings
            self.dirty = True
            if self.global_settings(app_name) == False:
                return

        self.set('Application', app_name)

        if self.settings.get('Created') is None:
            now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            log.info(f'Settings created at: {now}')
            self.set('Created', now)


    def get_last_error(self):
        err = self.last_error  # returns None if all OK
        self.last_error = None
        return err

    def set_last_error(self, error):
        self.last_error = error
        log.error(error)


    def set_path(self, path, file, must_exist=False):
        try:
            p = Path(path)
        except:
            self.set_last_error(f'Error in  path: {path}')
            return False

        p = p.joinpath(p, file)
        if must_exist == True and p.is_file() == False:
            self.set_last_error(f'{path} or {file} does not exist')
            return False

        self.path = p

        log.info(f'Path: {self.path}')
        return True

    def global_settings(self, app_name):
        # everybody else does it on windows, so it must be OK
        path = os.path.expanduser(os.path.join('~', '.VIRTUALROBOT', app_name))
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
        if self.path is None:
            log.info('Path is not set')
            return False

        if self.path.exists() == False:
            log.info('File {self.path} does not exist')
            return False

        try:
            with self.path.open() as json_file:
                settings = json.load(json_file)
                app = settings.get('Application')
                if app is None or app != self.app_name:
                    self.set_last_error(f'Bad settings file: {self.path}')
                    return False
        except:
            self.set_last_error( f'Error opening settings at: {self.path}')
            return False

        self.settings = settings
        self.dump()
        return True
              

    def save(self):
        if self.path is None:
            log.info('File is not set')
            return False

        try:
            with self.path.open('w') as outfile:
                json.dump(self.settings, outfile, indent=4, ensure_ascii=True)
        except:
            self.set_last_error(f'Error saving settings, path: {self.path}')
            return False

        return True

    def set(self, name, value):
        if isinstance(name, str) == False:
            self.set_last_error(f'Set name must be a string, got: {name}')
            return False

        self.settings[name] = value

        log.info(f'Settings set: {name}, {value}')

        if self.dirty:
            self.save()

        return True

    def get(self, name, default_value=None):
        """
        if not in settings, set default value
        """
        if isinstance(name, str) == False:
            log.error(f'Get name must be a string, got: {name}')
            return None

        value = self.settings.get(name)
        if value is None and default_value is not None:
            log.info(f'Setting default: {name} to {default_value}')
            self.set(name, default_value)
            return default_value

        log.info(f'Get: {name}: {value}')
        return value

    def dump(self):
        for k in self.settings.keys():
            v = self.settings[k]
            log.info(f'Stored setting: {k}, {v}')


    def close(self):
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

