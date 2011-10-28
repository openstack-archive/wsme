import unittest
from wsme import types


def gen_class():
    d = {}
    exec('''class tmp(object): pass''', d)
    return d['tmp']


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

        assert attrs[0].key == 'aint'
        assert isinstance(attrs[0], types.wsattr)
        assert attrs[0].datatype == int
        assert attrs[0].mandatory == False
        assert attrs[1].key == 'astr'
        assert attrs[2].key == 'auni'
        assert attrs[3].key == 'afloat'

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
        assert ForcedOrder._wsme_attributes[0].key == 'a2'
        assert ForcedOrder._wsme_attributes[1].key == 'a1'
        assert ForcedOrder._wsme_attributes[2].key == 'a3'

        c = gen_class()
        print c
        types.register_type(c)
        del c._wsme_attributes

        c.a2 = int
        c.a1 = int
        c.a3 = int

        types.register_type(c)

        assert c._wsme_attributes[0].key == 'a1'
        assert c._wsme_attributes[1].key == 'a2'
        assert c._wsme_attributes[2].key == 'a3'

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

        print WithWSProp._wsme_attributes
        assert len(WithWSProp._wsme_attributes) == 1
        a = WithWSProp._wsme_attributes[0]
        assert a.key == 'aint'
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

    def test_inspect_with_inheritance(self):
        class Parent(object):
            parent_attribute = int

        class Child(Parent):
            child_attribute = int

        types.register_type(Child)

    def test_selfreftype(self):
        class SelfRefType(object):
            pass

        SelfRefType.parent = SelfRefType

        types.register_type(SelfRefType)

    def test_inspect_with_property(self):
        class AType(object):
            @property
            def test(self):
                return 'test'

        types.register_type(AType)

        assert len(AType._wsme_attributes) == 0
        assert AType().test == 'test'
