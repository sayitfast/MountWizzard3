# -*- mode: python -*-
#
# to remember: import astropy.tests from __init__.py was removed manually
#
block_cipher = None
DISTPATH = '../dist'
WORKPATH = '../build'


a = Analysis(['mountwizzard3/mountwizzard3.py'],
             pathex=['/Users/mw/PycharmProjects/MountWizzard3/mountwizzard3'],
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
             hiddenimports=[
             'numpy.lib.recfunctions',
             'xml.dom',
             'shelve',          # shelve is for astropy
             'PyQt5.sip',       # not bundled for pyqt5 >5.11 anymore
              ],
             hookspath=[],
             runtime_hooks=[],
             excludes=['FixTk', 'tcl', 'tk', '_tkinter', 'tkinter', 'Tkinter', 'astropy'],
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
          name='mountwizzard3',
          debug=True,
          strip=True,
          upx=True,
          console=True,
          # onefile=True,
          onedir=True,
          icon='./mountwizzard3/icons/mw.icns',
          # exclude_binaries=True,
          )

#coll = COLLECT(exe,
#               a.binaries,
#               a.zipfiles,
#               a.datas,
#               strip=False,
#               upx=True,
#               name='mountwizzard3')

app = BUNDLE(exe,
             name='MountWizzard3.app',
             version=3,
             icon='./mountwizzard3/icons/mw.icns',
             bundle_identifier=None)

# rename the file to version number
# import build.build
# BUILD_NO = build.build.BUILD().BUILD_NO_FILE
# if file present, delete it
#if os.path.isfile(os.getcwd() + '\dist\mountwizzard3-console-' + BUILD_NO + '.exe'):
#    os.remove(os.getcwd() + '\dist\mountwizzard3-console-' + BUILD_NO + '.exe')
#os.rename(os.getcwd() + '\dist\mountwizzard3-console.exe', os.getcwd() + '\dist\mountwizzard3-console-' + BUILD_NO + '.exe')