# encoding=utf8

import unittest

from wsme import WSRoot
from wsme.protocols import getprotocol, CallContext
import wsme.protocols


class DummyProtocol(object):
    name = 'dummy'
    content_types = ['', None]

    def __init__(self):
        self.hits = 0

    def accept(self, req):
        return True

    def iter_calls(self, req):
        yield CallContext(req)

    def extract_path(self, context):
        return ['touch']

    def read_arguments(self, context):
        self.lastreq = context.request
        self.hits += 1
        return {}

    def encode_result(self, context, result):
        return str(result)

    def encode_error(self, context, infos):
        return str(infos)


def test_getprotocol():
    try:
        getprotocol('invalid')
        assert False, "ValueError was not raised"
    except ValueError, e:
        pass


class TestProtocols(unittest.TestCase):
    def test_register_protocol(self):
        wsme.protocols.register_protocol(DummyProtocol)
        assert wsme.protocols.registered_protocols['dummy'] == DummyProtocol

        r = WSRoot()
        assert len(r.protocols) == 0

        r.addprotocol('dummy')
        assert len(r.protocols) == 1
        assert r.protocols[0].__class__ == DummyProtocol

        r = WSRoot(['dummy'])
        assert len(r.protocols) == 1
        assert r.protocols[0].__class__ == DummyProtocol
