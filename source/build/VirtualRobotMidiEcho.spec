# -*- mode: python ; coding: utf-8 -*-
from kivy_deps import sdl2, glew
# kivy min
from kivy.tools.packaging.pyinstaller_hooks import get_deps_minimal, get_deps_all, hookspath, runtime_hooks

block_cipher = None


a = Analysis([  '..\\ui\\mainecho.py',
                '..\\midiapps\\midi_echo.py',
                '..\\midiapps\\midi_effect_manager.py',
                '..\\common\\midi.py',
                '..\\common\\upper_class_utils.py'
                ],
             pathex=['C:\\projects\\virtualrobotcompany\\bgunnison\\virtualrobot\\source\\build'],
             binaries=[ ('../ui/mainecho.kv', '.'), 
                        ('../ui/media/logo.zip', 'media'),
                        ('../ui/media/red_led.png', 'media'),
                        ('../ui/media/off_led.png', 'media'),
                        ('../ui/media/start_panic.png', 'media'),
                        ('../ui/media/end_panic.png', 'media'),

                        ],
             datas=[],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             #hookspath=hookspath(), # kivy min
             #runtime_hooks=runtime_hooks(), # kivy min
             #excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False,
             #**get_deps_minimal(video=None, audio=None) # kivy min
             ) 
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='VirtualRobotMidiEcho',
          icon='logo.ico',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False 
          )
coll = COLLECT(exe,
              
               a.binaries,
               a.zipfiles,
               a.datas,
               *[Tree(p) for p in (sdl2.dep_bins + glew.dep_bins)],
               strip=False,
               upx=True,
               upx_exclude=[],
               name='VirtualRobotMidiEcho')
