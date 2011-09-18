import unittest
from webob.dec import wsgify
from webtest import TestApp

from wsme import *

class WSTestRoot(WSRoot):
    def reset(self):
        self.touched = False

    @expose()
    def touch(self):
        self.touched = True

class TestProtocol(unittest.TestCase):
    def setUp(self):
        self.root = WSTestRoot([self.protocol])

        self.app = TestApp(wsgify(self.root._handle_request))

    def _call(self, fpath, **kw):
        pass
    
    def test_touch(self):
        assert self.call('touch') is None

