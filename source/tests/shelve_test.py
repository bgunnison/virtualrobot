"""
 Copyright (C) 2020 Brian R. Gunnison
 
 This file tests shelving

 This file can not be copied and/or distributed without the express
 permission of Brian R. Gunnison
"""
import sys
import os
import time
import logging


logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from common.upper_class_utils import Settings

title = 'MidiChord'
settings = Settings(title, debug_info=True)    # our persistant settings
settings.close()
print('Shelf test finished')

