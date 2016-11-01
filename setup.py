from distutils.core import setup

setup(
    name='mountwizzard',
    version='0.16',
    packages=[
        'mountwizzard',
        'mountwizzard/support',
    ],
    package_data={'mountwizzard': ['config/*', 'analysedata/*', 'images/*']},
    include_package_data=True,
    url='https://pypi.python.org/pypi/mountwizzard',
    license='APL 2.0',
    author='mw',
    author_email='michael@wuertenberger.org',
    description='tooling for a 10micron mount',
)
