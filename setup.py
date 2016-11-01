from distutils.core import setup

setup(
    name='mountwizzard',
    version='0.11',
    packages=[
        'mountwizzard',
        'mountwizzard/analyse',
        'mountwizzard/model_thread',
        'mountwizzard/mount_thread',
        'mountwizzard/mount_ui',
        'mountwizzard/relays',
        'mountwizzard/sgpro',
        'mountwizzard/stick_thread',
        'mountwizzard/weather_thread'
    ],
    url='https://pypi.python.org/pypi/mountwizzard',
    license='APL 2.0',
    author='mw',
    author_email='michael@wuertenberger.org',
    description='tooling for a 10micron mount',
)
