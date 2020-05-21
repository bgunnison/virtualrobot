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
    def __init__(self, app_name='generic', debug_info=False):
        """
        Try to make this foolproof...
        put settings in user dir in case other dirs are admin
        we create the path dirs
        then create the shelve files, if these fail we resort to a dictionay so set and get work, but persistance fails
        todo: multiple apps of same type?
        """
        self.debug_info = debug_info
        self.path = os.path.expanduser(os.path.join('~', 'AppData', 'Local', 'VIRTUALROBOT', app_name))
        self.debug_log(f'Path: {self.path}')
        self.settings = None
        self.persist = True
        self.closed = True

        self._open()    
        if self.dump() == False: # getting a exception dumping, try saving first
            self.delete_config()
            self._open()


        now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        #log.info(f'Settings at {self.path} started: {now}')
        self.set(app_name, now)
        self.set('path', self.path)
        self.save()

    def debug_log(self, msg):
        if self.debug_info:
            log.info(msg)
     
    def delete_config(self):
        self.debug_log('Deleting settings files')
        thispath = os.path.join(self.path, '*')
        files = glob.glob(thispath)
        for file in files:
            if 'config' in file:
                self.debug_log(f'Removing: {file}')
                os.remove(file)

    def _open(self):
        # flag = 'n'  # NOT ON WINDOWS!! Always create a new, empty database, open for reading and writing
        try:
            if Path(self.path).exists() == False:
                self.debug_log(f'Creating settings path: {self.path}')
                Path(self.path).mkdir(parents=True)

            pathfile = os.path.join(self.path, 'config')
            self.debug_log(f'Settings opening at: {pathfile}')
            self.settings = shelve.open(pathfile, writeback=True) # we do not want to save every access only when closed
            self.persist = True
            self.closed = False
        except:
            log.error(f'Error opening settings at: {self.path}')
            self.settings = {}  # use a dict so all the calls don't fail and we can get settings
            self.persist = False

    def save(self):
        if self.persist:
            try:
                self.settings.sync()
            except:
                log.error('Error syncing settings')

    def set(self, name, value):
        try:
            self.settings[name] = value
        except:
            log.error(f'Error setting: {name} to {value}')
            return

        self.debug_log(f'Settings set: {self.path}, {name}, {value}')

    def get(self, name, default_value=None):
        """
        if not in settings, set default value
        """
        try:
            value = self.settings[name]
        except:
            self.debug_log(f'Setting default: {name} to {default_value}')
            self.set(name, default_value)
            return default_value

        self.debug_log(f'Get: {name}: {value}')
        return value

    def dump(self):
        try:
            for k in self.settings.keys():
                v = self.settings[k]
                self.debug_log(f'Stored setting: {k}, {v}')
        except:
            log.error('Settings dump encountered an error')
            try:
                self.settings.close()
            except:
                log.error('Cant close after dump error')
            return False # a bad config file

        return True


    def close(self):
        if self.closed:
            self.debug_log('Already closed')
            return

        self.debug_log('Closing')
        self.dump()
        if self.persist:
            try:
                self.closed = True
                self.settings.close()
            except:
                log.error('Error closing')
                return

        self.debug_log(f'Settings closed {self.path}')

    def __del__(self):
        self.debug_log('Deleting')
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

