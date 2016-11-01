from distutils.core import setup

setup(
    name='mountwizzard',
    version='0.13',
    packages=[
        'mountwizzard',
        'mountwizzard/support',
    ],
    url='https://pypi.python.org/pypi/mountwizzard',
    license='APL 2.0',
    author='mw',
    author_email='michael@wuertenberger.org',
    description='tooling for a 10micron mount',
)
