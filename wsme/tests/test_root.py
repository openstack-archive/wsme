# encoding=utf8

import unittest

from wsme import WSRoot


class TestRoot(unittest.TestCase):
    def test_default_transaction(self):
        import transaction
        root = WSRoot(transaction=True)
        assert root._transaction is transaction

        txn = root.begin()
        txn.abort()
