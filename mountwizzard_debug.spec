# -*- mode: python -*-
#
# to remember: import astropy.tests from __init__.py was removed manually
#
block_cipher = None
import sys
sys.modules['FixTk'] = None
DISTPATH = '../dist'
WORKPATH = '../build'

a = Analysis(['mountwizzard3\\mountwizzard3.py'],
             pathex=['C:\\Users\\mw\\Projects\\MountWizzard3\\mountwizzard3'],
             binaries=[],
             datas=[
             ('C:\\Program Files (x86)\\Python36-32\\Lib\\site-packages\\astropy\\io\\fits', '.\\astropy\\io\\fits'),
             ('C:\\Program Files (x86)\\Python36-32\\Lib\\site-packages\\astropy\\io\\__init__.py', '.\\astropy\\io'),
             ('C:\\Program Files (x86)\\Python36-32\\Lib\\site-packages\\astropy\\_erfa', '.\\astropy\\_erfa'),
             ('C:\\Program Files (x86)\\Python36-32\\Lib\\site-packages\\astropy\\utils', '.\\astropy\\utils'),
             ('C:\\Program Files (x86)\\Python36-32\\Lib\\site-packages\\astropy\\logger.py', '.\\astropy'),
             ('C:\\Program Files (x86)\\Python36-32\\Lib\\site-packages\\astropy\\config', '.\\astropy\\config'),
             ('C:\\Program Files (x86)\\Python36-32\\Lib\\site-packages\\astropy\\units', '.\\astropy\\units'),
             ('C:\\Program Files (x86)\\Python36-32\\Lib\\site-packages\\astropy\\constants', '.\\astropy\\constants'),
             ('C:\\Program Files (x86)\\Python36-32\\Lib\\site-packages\\astropy\\visualization', '.\\astropy\\visualization'),
             ('C:\\Program Files (x86)\\Python36-32\\Lib\\site-packages\\astropy\\stats', '.\\astropy\\stats'),
             ('C:\\Program Files (x86)\\Python36-32\\Lib\\site-packages\\astropy\\extern', '.\\astropy\\extern'),
             ('C:\\Program Files (x86)\\Python36-32\\Lib\\site-packages\\astropy\\__init__.py', '.\\astropy'),
             ('C:\\Program Files (x86)\\Python36-32\\Lib\\site-packages\\astropy\\astropy.cfg', '.\\astropy'),
             # for adding coordinates
             #('C:\\Program Files (x86)\\Python36-32\\Lib\\site-packages\\astropy\\coordinates', '.\\astropy\\coordinates'),
             #('C:\\Program Files (x86)\\Python36-32\\Lib\\site-packages\\astropy\\time', '.\\astropy\\time'),
             #('C:\\Program Files (x86)\\Python36-32\\Lib\\site-packages\\astropy\\table', '.\\astropy\\table'),
             #('C:\\Program Files (x86)\\Python36-32\\Lib\\site-packages\\astropy\\io', '.\\astropy\\io'),
             #('C:\\Program Files (x86)\\Python36-32\\Lib\\site-packages\\astropy\\wcs', '.\\astropy\\wcs'),
             ],
             hiddenimports=['numpy.lib.recfunctions','xml.dom', 'shelve'],    # shelve is for astropy
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
          name='mountwizzard3-console',
          debug=True,
          strip=False,
          upx=False,
          console=True,
          icon='mountwizzard3\\icons\\mw.ico')

#######################################
# Code-sign the generated executable
import subprocess
import os
subprocess.call('c:\signtool\signtool.exe sign /tr http://timestamp.digicert.com /td sha256 /fd sha256 /f c:\signtool\mountwizzard.pfx /p saturn ' + os.getcwd() + '\dist\mountwizzard3-console.exe')
#######################################