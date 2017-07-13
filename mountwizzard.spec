# -*- mode: python -*-

block_cipher = None

import sys
sys.modules['FixTk'] = None

a = Analysis(['mountwizzard.py'],
             pathex=['C:\\Program Files (x86)\\Python35-32\\Lib\\site-packages\\PyQt5\\Qt\\bin', 'C:\\Users\\mw\\Projects\\mountwizzard'],
             binaries=[],
             datas=[('model001.fit','.')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=['FixTk', 'tcl', 'tk', '_tkinter', 'tkinter', 'Tkinter'],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)

pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='mountwizzard',
          debug=False,
          strip=False,
          upx=False,
          console=False,
          icon='./mw.ico')


#######################################
# Code-sign the generated executable
#import subprocess
#subprocess.call([
#   "SIGNTOOL.EXE",
#   "/F", "path-to-key.pfx",
#   "/P", "your-password",
#   "/T", "time-stamping url",
#   'mountwizzard.exe',
#])
#######################################