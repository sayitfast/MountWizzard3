# -*- mode: python -*-

block_cipher = None

import sys
sys.modules['FixTk'] = None
DISTPATH = '../dist'
WORKPATH = '../build'

a = Analysis(['mountwizzard\\mountwizzard.py'],
             pathex=['C:\\Program Files (x86)\\Python35-32\\Lib\\site-packages\\PyQt5\\Qt\\bin', 'C:\\Users\\mw\\Projects\\mountwizzard\\mountwizzard'],
             binaries=[],
             datas=[('mountwizzard\\model001.fit','.')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=['FixTk', 'tcl', 'tk', '_tkinter', 'tkinter', 'Tkinter'],
             win_no_prefer_redirects=True,
             win_private_assemblies=True,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='mountwizzard-console',
          debug=True,
          strip=False,
          upx=False,
          console=True,
          icon='mountwizzard\\mw.ico')
