# -*- mode: python -*-
#
# to remember: import astropy.tests from __init__.py was removed manually
#
block_cipher = None
import sys
sys.modules['FixTk'] = None
DISTPATH = '../dist'
WORKPATH = '../build'

a = Analysis(['mountwizzard/mountwizzard.py'],
             pathex=['/Users/mw/PycharmProjects/MountWizzard3/mountwizzard'],
             binaries=[],
             datas=[
             ('/Library/Frameworks/Python.framework/Versions/3.6/lib/python3.6/site-packages/astropy/io/fits', './astropy/io/fits'),
             ('/Library/Frameworks/Python.framework/Versions/3.6/lib/python3.6/site-packages/astropy/io/__init__.py', './astropy/io'),
             ('/Library/Frameworks/Python.framework/Versions/3.6/lib/python3.6/site-packages/astropy/_erfa', './astropy/_erfa'),
             ('/Library/Frameworks/Python.framework/Versions/3.6/lib/python3.6/site-packages/astropy/utils', './astropy/utils'),
             ('/Library/Frameworks/Python.framework/Versions/3.6/lib/python3.6/site-packages/astropy/logger.py', './astropy'),
             ('/Library/Frameworks/Python.framework/Versions/3.6/lib/python3.6/site-packages/astropy/config', './astropy/config'),
             ('/Library/Frameworks/Python.framework/Versions/3.6/lib/python3.6/site-packages/astropy/units', './astropy/units'),
             ('/Library/Frameworks/Python.framework/Versions/3.6/lib/python3.6/site-packages/astropy/constants', './astropy/constants'),
             ('/Library/Frameworks/Python.framework/Versions/3.6/lib/python3.6/site-packages/astropy/visualization', './astropy/visualization'),
             ('/Library/Frameworks/Python.framework/Versions/3.6/lib/python3.6/site-packages/astropy/stats', './astropy/stats'),
             ('/Library/Frameworks/Python.framework/Versions/3.6/lib/python3.6/site-packages/astropy/extern', './astropy/extern'),
             ('/Library/Frameworks/Python.framework/Versions/3.6/lib/python3.6/site-packages/astropy/__init__.py', './astropy'),
             ('/Library/Frameworks/Python.framework/Versions/3.6/lib/python3.6/site-packages/astropy/astropy.cfg', './astropy'),
             ],
             hiddenimports=['numpy.lib.recfunctions','xml.dom'],
             hookspath=[],
             runtime_hooks=[],
             excludes=['FixTk', 'tcl', 'tk', '_tkinter', 'tkinter', 'Tkinter', 'tornado', 'astropy'],
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
          icon='mountwizzard/icons/mw.ico')
