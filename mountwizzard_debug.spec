# -*- mode: python -*-

block_cipher = None

import sys
sys.modules['FixTk'] = None
DISTPATH = '../dist'
WORKPATH = '../build'

a = Analysis(['mountwizzard\\mountwizzard.py'],
             pathex=['C:\\Users\\mw\\Projects\\MountWizzard3\\mountwizzard'],
             # pathex=['C:\\Program Files (x86)\\Python35-32\\Lib\\site-packages\\PyQt5\\Qt\\bin', 'C:\\Users\\mw\\Projects\\MountWizzard3\\mountwizzard'],
             binaries=[],
             datas=[
             ('C:\\Program Files (x86)\\Python35-32\\Lib\\site-packages\\astropy', '.\\astropy'),
             ],
             hiddenimports=['numpy.lib.recfunctions','xml.dom'],
             hookspath=[],
             runtime_hooks=[],
             excludes=['FixTk', 'tcl', 'tk', '_tkinter', 'tkinter', 'Tkinter', 'astropy'],
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
          icon='mountwizzard\\icons\\mw.ico')
