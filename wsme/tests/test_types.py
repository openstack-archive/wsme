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
        attrs = Flat._wsme_attributes
        print attrs

        assert attrs[0][0] == 'aint'
        assert isinstance(attrs[0][1], types.wsattr)
        assert attrs[0][1].datatype == int
        assert attrs[0][1].mandatory == False
        assert attrs[1][0] == 'astr'
        assert attrs[2][0] == 'auni'
        assert attrs[3][0] == 'afloat'

    def test_private_attr(self):
        class WithPrivateAttrs(object):
            _private = 12

        types.register_type(WithPrivateAttrs)

        assert len(WithPrivateAttrs._wsme_attributes) == 0

    def test_attribute_order(self):
        class ForcedOrder(object):
            _wsme_attr_order = ('a2', 'a1', 'a3')
            a1 = int
            a2 = int
            a3 = int

        types.register_type(ForcedOrder)

        print ForcedOrder._wsme_attributes
        assert ForcedOrder._wsme_attributes[0][0] == 'a2'
        assert ForcedOrder._wsme_attributes[1][0] == 'a1'
        assert ForcedOrder._wsme_attributes[2][0] == 'a3'

    def test_wsproperty(self):
        class WithWSProp(object):
            def __init__(self):
                self._aint = 0

            def get_aint(self):
                return self._aint

            def set_aint(self, value):
                self._aint = value

            aint = types.wsproperty(int, get_aint, set_aint, mandatory=True)

        types.register_type(WithWSProp)

        assert len(WithWSProp._wsme_attributes) == 1
        a = WithWSProp._wsme_attributes[0][1]
        assert a.datatype == int
        assert a.mandatory

        o = WithWSProp()
        o.aint = 12

        assert o.aint == 12

    def test_nested(self):
        class Inner(object):
            aint = int

        class Outer(object):
            inner = Inner

        types.register_type(Outer)

        assert hasattr(Inner, '_wsme_attributes')
        assert len(Inner._wsme_attributes) == 1
