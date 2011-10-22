import os

from setuptools import setup

execfile(os.path.join('wsme', 'release.py'))

long_description = open("README").read()

setup(
    name=name,
    version=version,
    description=description,
    long_description=long_description,
    author=author,
    author_email=email,
    url=url,
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
