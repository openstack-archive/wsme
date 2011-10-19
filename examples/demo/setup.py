from setuptools import setup

setup(name='demo',
    install_requires=[
        'WSME',
        'WSME-Soap',
        'PasteScript',
        'PasteDeploy',
        'WSGIUtils',
        'Pygments',
    ],
    package=['demo'])
