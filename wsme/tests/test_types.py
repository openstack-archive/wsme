import unittest
from wsme import types

class TestTypes(unittest.TestCase):
    def test_flat_type(self):
        class Flat(object):
            aint = int
            astr = str
            auni = unicode
            afloat = float

        types.register_type(Flat)

        assert len(Flat._wsme_attributes) == 4

    def test_private_attr(self):
        class WithPrivateAttrs(object):
            _private = 12
        
        types.register_type(WithPrivateAttrs)

        assert len(WithPrivateAttrs._wsme_attributes) == 0

