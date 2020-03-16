"""
 Copyright (C) 2020 Brian R. Gunnison
 
 This file is part of MIDI project
 
 MIDI can not be copied and/or distributed without the express
 permission of Brian R. Gunnison

 https://build-system.fman.io/generating-license-keys
"""
import os
import sys
import rsa # pip install rsa
from base64 import b64decode                                         
import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


class License:
    def __init__(self):
        self.valid = False

    def verify(self, email, signature, pubkey=None, settings=None):
        if settings is not None:
            pubkey = settings.get('MyCompanyPublicKey', '')

        s = b64decode(signature)

        try:
            rsa.verify(email.encode('utf-8'), s, pubkey)
        except rsa.VerificationError:
            log.error(f'Invalid key: {email}')
            return

        log.info(f'Valid key: {email}')
        self.valid = True

    def is_valid(self):
        return self.valid

