from setuptools import setup
import sys

if sys.version_info[:2] <= (2, 5):
    webob_version = ' <= 1.1.1'
elif sys.version_info[:2] >= (3, 0):
    webob_version = ' >= 1.2.2'
else:
    webob_version = ''

install_requires = [
    'six',
    'simplegeneric',
    'WebOb' + webob_version
]

if sys.version_info[:2] <= (2, 6):
    install_requires += ('ordereddict',)

if sys.version_info[:2] < (3, 3):
    install_requires += ('ipaddr',)

setup(
    setup_requires=['pbr>=0.5.21'],
    install_requires=install_requires,
    pbr=True
)
