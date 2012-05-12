# encoding=utf8

import unittest

from wsme import WSRoot
from wsme.root import default_prepare_response_body

from six import b, u


class TestRoot(unittest.TestCase):
    def test_default_transaction(self):
        import transaction
        root = WSRoot(transaction=True)
        assert root._transaction is transaction

        txn = root.begin()
        txn.abort()

    def test_default_prepare_response_body(self):
        default_prepare_response_body(None, [b('a')]) == b('a')
        default_prepare_response_body(None, [b('a'), b('b')]) == b('a\nb')
        default_prepare_response_body(None, [u('a')]) == u('a')
        default_prepare_response_body(None, [u('a'), u('b')]) == u('a\nb')

    def test_protocol_selection_error(self):
        import wsme.protocols

        class P(wsme.protocols.Protocol):
            def accept(self, r):
                raise Exception('test')

        root = WSRoot()
        root.addprotocol(P())

        from webob import Request
        req = Request.blank('/test?check=a&check=b&name=Bob')
        res = root._handle_request(req)
        assert res.status_int == 500
        assert res.content_type == 'text/plain'
        assert res.text == u('Error while selecting protocol: test'), req.text
