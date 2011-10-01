import os

from setuptools import setup

execfile(os.path.join('wsme', 'release.py'))

setup(
    name=name,
    version=version,
    description=description,
    long_description=long_description,
    author=author,
    author_email=email,
    url=url,
    packages=['wsme'],
    install_requires=[
        'simplegeneric',
        'webob',
    ],
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: WSGI'
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)
