import unittest
import sphinx
import os.path

import wsme.types

docpath = os.path.join(
    os.path.dirname(__file__),
    'sphinxexample')


class ASampleType(object):
    somebytes = wsme.types.bytes
    sometext = wsme.types.text
    someint = int


class TestSphinxExt(unittest.TestCase):
    def test_buildhtml(self):
        if not os.path.exists('.test_sphinxext/'):
            os.makedirs('.test_sphinxext/')
        assert sphinx.main(['',
            '-b', 'html',
            '-d', '.test_sphinxext/doctree',
            docpath,
            '.test_sphinxext/html']) == 0
