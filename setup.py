# from distutils.core import setup
from setuptools import setup
import mountwizzard3.build.build
import platform

setup(
    name='mountwizzard3',
    version=mountwizzard3.build.build.BUILD().BUILD_NO_FILE,
    packages=[
        'mountwizzard3',
        'mountwizzard3.analyse',
        'mountwizzard3.ascom',
        'mountwizzard3.astrometry',
        'mountwizzard3.audio',
        'mountwizzard3.build',
        'mountwizzard3.automation',
        'mountwizzard3.baseclasses',
        'mountwizzard3.imaging',
        'mountwizzard3.dome',
        'mountwizzard3.environment',
        'mountwizzard3.gui',
        'mountwizzard3.icons',
        'mountwizzard3.indi',
        'mountwizzard3.modeling',
        'mountwizzard3.mount',
        'mountwizzard3.relays',
        'mountwizzard3.remote',
        'mountwizzard3.widgets'
    ],
    python_requires='~=3.6.3',
    install_requires=[
        'PyQt5==5.11.2',
        'matplotlib==2.2.2',
        'wakeonlan>=1.0.0',
        'requests==2.18.4',
        'astropy==3.0.3',
        'numpy==1.14.0',
        'requests_toolbelt==0.8.0'
    ]
    + (['pypiwin32==220'] if "Windows" == platform.system() else [])
    + (['pywinauto==0.6.4'] if "Windows" == platform.system() else [])
    + (['comtypes==1.1.1'] if "Windows" == platform.system() else [])
    ,
    url='https://github.com/mworion/MountWizzard3-DIST',
    license='APL 2.0',
    author='mw',
    author_email='michael@wuertenberger.org',
    description='tooling for a 10micron mount',
)

if platform.system() == 'Linux':
    print('#############################################')
    print('### Important hint:                       ###')
    print('### There might be the need to install    ###')
    print('### libfreetype6-dev manually as well     ###')
    print('### sudo apt-get install libfreetype6-dev ###')
    print('#############################################')

