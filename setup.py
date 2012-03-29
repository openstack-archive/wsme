import os

from setuptools import setup

filename = os.path.join('wsme', 'release.py')
release = {}
exec(compile(open(filename).read(), filename, 'exec'), release)

long_description = open("README", 'rt').read()

setup(
    name=release['name'],
    version=release['version'],
    description=release['description'],
    long_description=long_description,
    author=release['author'],
    author_email=release['email'],
    url=release['url'],
    packages=['wsme', 'wsme.protocols'],
    package_data={
        'wsme.protocols': ['templates/*.html'],
    },
    install_requires=[
        'simplegeneric',
        'webob',
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
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
