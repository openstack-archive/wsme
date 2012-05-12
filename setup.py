import os
import sys

from setuptools import setup

filename = os.path.join('wsme', 'release.py')
release = {}
exec(compile(open(filename).read(), filename, 'exec'), release)

long_description = open("README.rst", 'rt').read()

if sys.version_info[:2] <= (2, 5):
    webob_version = '<=1.1.1'
elif sys.version_info[:2] >= (3, 0):
    webob_version = '>=1.2b3'
else:
    webob_version = ''

setup(
    name=release['name'],
    version=release['version'],
    description=release['description'],
    long_description=long_description,
    author=release['author'],
    author_email=release['email'],
    url=release['url'],
    packages=['wsme', 'wsme.protocols', 'wsme.tests'],
    package_data={
        'wsme.protocols': ['templates/*.html'],
    },
    install_requires=[
        'six',
        'simplegeneric',
        'webob' + webob_version
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.5',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'License :: OSI Approved :: MIT License',
        'Topic :: Internet :: WWW/HTTP :: WSGI',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],

    entry_points={
        'wsme.protocols': [
            'restjson = wsme.protocols.restjson:RestJsonProtocol',
            'restxml = wsme.protocols.restxml:RestXmlProtocol',
        ]
    },
)
