# from distutils.core import setup
from setuptools import setup

setup(
    name='mountwizzard',
    version='2.5.4.1',
    packages=[
        'analyse',
        'astrometry',
        'automation',
        'baseclasses',
        'camera',
        'dome',
        'environment',
        'gui',
        'modeling',
        'mount',
        'relays',
        'remote',
        'widgets'
    ],
    install_requires=[
        'PyQt5>=5.6',
        'matplotlib>=1.5.3',
        'pypiwin32>=219',
        'pyfits>=3.4',
        'wakeonlan>=0.2.2'
    ],
    url='https://pypi.python.org/pypi/mountwizzard',
    license='APL 2.0',
    author='mw',
    author_email='michael@wuertenberger.org',
    description='tooling for a 10micron mount',
)
