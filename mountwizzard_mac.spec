############################################################
# -*- coding: utf-8 -*-
#
#       #   #  #   #   #  ####
#      ##  ##  #  ##  #     #
#     # # # #  # # # #     ###
#    #  ##  #  ##  ##        #
#   #   #   #  #   #     ####
#
# Python-based Tool for interaction with the 10micron mounts
# GUI with PyQT5 for python
# Python  v3.6.5
#
# Michael Würtenberger
# (c) 2016, 2017, 2018
#
# Licence APL2.0
#
###########################################################
#
#
# to remember:  import astropy.tests from __init__.py was removed manually
#               hook for matplotlib was changed to use Qt5Agg only
#
import os
import shutil
DISTPATH = '../dist'
WORKPATH = '../build'

from PyInstaller.compat import modname_tkinter
import mountwizzard3.build.build


BUILD_NO = mountwizzard3.build.build.BUILD().BUILD_NO_FILE

block_cipher = None
pythonPath = '/Library/Frameworks/Python.framework/Versions/3.6/lib/python3.6'
astropyLibPath = pythonPath + '/site-packages/astropy'
distDir = '/Users/mw/PycharmProjects/MountWizzard3/dist'


a = Analysis(['mountwizzard3/mountwizzard3.py'],
    pathex=['/Users/mw/PycharmProjects/MountWizzard3/mountwizzard3'],
    binaries=[],
    datas=[
        (astropyLibPath + '/io/fits', './astropy/io/fits'),
        (astropyLibPath + '/io/__init__.py', './astropy/io'),
        (astropyLibPath + '/_erfa', './astropy/_erfa'),
        (astropyLibPath + '/utils', './astropy/utils'),
        (astropyLibPath + '/logger.py', './astropy'),
        (astropyLibPath + '/config', './astropy/config'),
        (astropyLibPath + '/units', './astropy/units'),
        (astropyLibPath + '/constants', './astropy/constants'),
        (astropyLibPath + '/visualization', './astropy/visualization'),
        (astropyLibPath + '/stats', './astropy/stats'),
        (astropyLibPath + '/extern', './astropy/extern'),
        (astropyLibPath + '/__init__.py', './astropy'),
        (astropyLibPath + '/astropy.cfg', './astropy'),
        ],
    hiddenimports=[
        'numpy.lib.recfunctions',
        'xml.dom',
        'shelve',          # shelve is for astropy
        'PyQt5.sip',       # not bundled for pyqt5 >5.11 anymore
        ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[
        'FixTk',
        'tcl',
        'tk',
        '_tkinter',
        'tkinter',
        'Tkinter',
        modname_tkinter
        ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher)

pyz = PYZ(a.pure,
        a.zipped_data,
        cipher=block_cipher
        )

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='mountwizzard3',
          debug=True,
          strip=True,
          upx=False,
          console=True,
          # onefile=True,
          onefile=True,
          icon='./mountwizzard3/icons/mw.icns',
          # exclude_binaries=True,
          )

#
# we have to prepare the build as there is an error when overwriting it
# if file present, we have to delete it
#

buildFile = distDir + '/MountWizzard3.app'
buildFileNumber = distDir + '/mountwizzard3-' + BUILD_NO + '.app'

print(BUILD_NO)

if os.path.isfile(buildFile):
    os.remove(buildFile)
    print('removed existing app bundle')

app = BUNDLE(exe,
             name='MountWizzard3.app',
             version=3,
             icon='./mountwizzard3/icons/mw.icns',
             bundle_identifier=None)

#
# we have to prepare the build as there is an error when overwriting it
# if file present, we have to delete it
#

if os.path.isdir(buildFileNumber):
    shutil.rmtree(buildFileNumber)
    print('removed existing app bundle with version number')

os.rename(buildFile, buildFileNumber)