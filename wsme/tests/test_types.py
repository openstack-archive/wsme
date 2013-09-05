import unittest
import sys
import six

from wsme import types


def gen_class():
    d = {}
    exec('''class tmp(object): pass''', d)
    return d['tmp']


class TestTypes(unittest.TestCase):
    def setUp(self):
        types.registry = types.Registry()

    def test_default_usertype(self):
        class MyType(types.UserType):
            basetype = str

        My = MyType()

        assert My.validate('a') == 'a'
        assert My.tobasetype('a') == 'a'
        assert My.frombasetype('a') == 'a'

    def test_unset(self):
        u = types.Unset

        assert not u

    def test_flat_type(self):
        class Flat(object):
            aint = int
            abytes = six.binary_type
            atext = six.text_type
            afloat = float

        types.register_type(Flat)

        assert len(Flat._wsme_attributes) == 4
        attrs = Flat._wsme_attributes
        print(attrs)

        assert attrs[0].key == 'aint'
        assert attrs[0].name == 'aint'
        assert isinstance(attrs[0], types.wsattr)
        assert attrs[0].datatype == int
        assert attrs[0].mandatory is False
        assert attrs[1].key == 'abytes'
        assert attrs[1].name == 'abytes'
        assert attrs[2].key == 'atext'
        assert attrs[2].name == 'atext'
        assert attrs[3].key == 'afloat'
        assert attrs[3].name == 'afloat'

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

        print(ForcedOrder._wsme_attributes)
        assert ForcedOrder._wsme_attributes[0].key == 'a2'
        assert ForcedOrder._wsme_attributes[1].key == 'a1'
        assert ForcedOrder._wsme_attributes[2].key == 'a3'

        c = gen_class()
        print(c)
        types.register_type(c)
        del c._wsme_attributes

        c.a2 = int
        c.a1 = int
        c.a3 = int

        types.register_type(c)

        assert c._wsme_attributes[0].key == 'a1', c._wsme_attributes[0].key
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

        print(WithWSProp._wsme_attributes)
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

        types.register_type(Parent)
        types.register_type(Child)

        assert len(Child._wsme_attributes) == 2

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

    def test_enum(self):
        aenum = types.Enum(str, 'v1', 'v2')
        assert aenum.basetype is str

        class AType(object):
            a = aenum

        types.register_type(AType)

        assert AType.a.datatype is aenum

        obj = AType()
        obj.a = 'v1'
        assert obj.a == 'v1', repr(obj.a)

        try:
            obj.a = 'v3'
            assert False, 'ValueError was not raised'
        except ValueError:
            e = sys.exc_info()[1]
            assert str(e) == \
                "a: Value 'v3' is invalid (should be one of: v1, v2)", e

    def test_attribute_validation(self):
        class AType(object):
            alist = [int]
            aint = int

        types.register_type(AType)

        obj = AType()

        obj.alist = [1, 2, 3]
        assert obj.alist == [1, 2, 3]
        obj.aint = 5
        assert obj.aint == 5

        self.assertRaises(ValueError, setattr, obj, 'alist', 12)
        self.assertRaises(ValueError, setattr, obj, 'alist', [2, 'a'])

    def test_text_attribute_conversion(self):
        class SType(object):
            atext = types.text
            abytes = types.bytes

        types.register_type(SType)

        obj = SType()

        obj.atext = six.b('somebytes')
        assert obj.atext == six.u('somebytes')
        assert isinstance(obj.atext, types.text)

        obj.abytes = six.u('sometext')
        assert obj.abytes == six.b('sometext')
        assert isinstance(obj.abytes, types.bytes)

    def test_named_attribute(self):
        class ABCDType(object):
            a_list = types.wsattr([int], name='a.list')
            astr = str

        types.register_type(ABCDType)

        assert len(ABCDType._wsme_attributes) == 2
        attrs = ABCDType._wsme_attributes

        assert attrs[0].key == 'a_list', attrs[0].key
        assert attrs[0].name == 'a.list', attrs[0].name
        assert attrs[1].key == 'astr', attrs[1].key
        assert attrs[1].name == 'astr', attrs[1].name

    def test_wsattr_del(self):
        class MyType(object):
            a = types.wsattr(int)

        types.register_type(MyType)

        value = MyType()

        value.a = 5
        assert value.a == 5
        del value.a
        assert value.a is types.Unset

    def test_validate_dict(self):
        assert types.validate_value({int: str}, {1: '1', 5: '5'})

        try:
            types.validate_value({int: str}, [])
            assert False, "No ValueError raised"
        except ValueError:
            pass

        assert types.validate_value({int: str}, {'1': '1', 5: '5'})

        try:
            types.validate_value({int: str}, {1: 1, 5: '5'})
            assert False, "No ValueError raised"
        except ValueError:
            pass

    def test_validate_list_valid(self):
        assert types.validate_value([int], [1, 2])
        assert types.validate_value([int], ['5'])

    def test_validate_list_empty(self):
        assert types.validate_value([int], []) == []

    def test_validate_list_none(self):
        v = types.ArrayType(int)
        assert v.validate(None) is None

    def test_validate_list_invalid_member(self):
        try:
            assert types.validate_value([int], ['not-a-number'])
            assert False, "No ValueError raised"
        except ValueError:
            pass

    def test_validate_list_invalid_type(self):
        try:
            assert types.validate_value([int], 1)
            assert False, "No ValueError raised"
        except ValueError:
            pass

    def test_validate_float(self):
        self.assertEqual(types.validate_value(float, 1), 1.0)
        self.assertEqual(types.validate_value(float, '1'), 1.0)
        self.assertEqual(types.validate_value(float, 1.1), 1.1)
        try:
            types.validate_value(float, [])
            assert False, "No ValueError raised"
        except ValueError:
            pass
        try:
            types.validate_value(float, 'not-a-float')
            assert False, "No ValueError raised"
        except ValueError:
            pass

    def test_validate_int(self):
        self.assertEqual(types.validate_value(int, 1), 1)
        self.assertEqual(types.validate_value(int, '1'), 1)
        self.assertEqual(types.validate_value(int, six.u('1')), 1)
        try:
            types.validate_value(int, 1.1)
            assert False, "No ValueError raised"
        except ValueError:
            pass

    def test_register_invalid_array(self):
        self.assertRaises(ValueError, types.register_type, [])
        self.assertRaises(ValueError, types.register_type, [int, str])
        self.assertRaises(AttributeError, types.register_type, [1])

    def test_register_invalid_dict(self):
        self.assertRaises(ValueError, types.register_type, {})
        self.assertRaises(ValueError, types.register_type,
                          {int: str, str: int})
        self.assertRaises(ValueError, types.register_type,
                          {types.Unset: str})

    def test_list_attribute_no_auto_register(self):
        class MyType(object):
            aint = int

        assert not hasattr(MyType, '_wsme_attributes')

        try:
            types.list_attributes(MyType)
            assert False, "TypeError was not raised"
        except TypeError:
            pass

        assert not hasattr(MyType, '_wsme_attributes')

    def test_list_of_complextypes(self):
        class A(object):
            bs = types.wsattr(['B'])

        class B(object):
            i = int

        types.register_type(A)
        types.register_type(B)

        assert A.bs.datatype.item_type is B

    def test_cross_referenced_types(self):
        class A(object):
            b = types.wsattr('B')

        class B(object):
            a = A

        types.register_type(A)
        types.register_type(B)

        assert A.b.datatype is B

    def test_base(self):
        class B1(types.Base):
            b2 = types.wsattr('B2')

        class B2(types.Base):
            b2 = types.wsattr('B2')

        assert B1.b2.datatype is B2, repr(B1.b2.datatype)
        assert B2.b2.datatype is B2

    def test_base_init(self):
        class C1(types.Base):
            s = six.text_type

        c = C1(s=six.u('test'))
        assert c.s == six.u('test')

    def test_array_eq(self):
        l = [types.ArrayType(str)]
        assert types.ArrayType(str) in l

    def test_array_sample(self):
        s = types.ArrayType(str).sample()
        assert isinstance(s, list)
        assert s
        assert s[0] == ''

    def test_dict_sample(self):
        s = types.DictType(str, str).sample()
        assert isinstance(s, dict)
        assert s
        assert s == {'': ''}

    def test_binary_to_base(self):
        import base64
        assert types.binary.tobasetype(None) is None
        expected = base64.encodestring(six.b('abcdef'))
        assert types.binary.tobasetype(six.b('abcdef')) == expected

    def test_binary_from_base(self):
        import base64
        assert types.binary.frombasetype(None) is None
        encoded = base64.encodestring(six.b('abcdef'))
        assert types.binary.frombasetype(encoded) == six.b('abcdef')

    def test_wsattr_weakref_datatype(self):
        # If the datatype inside the wsattr ends up a weakref, it
        # should be converted to the real type when accessed again by
        # the property getter.
        import weakref
        a = types.wsattr(int)
        a.datatype = weakref.ref(int)
        assert a.datatype is int

    def test_wsattr_list_datatype(self):
        # If the datatype inside the wsattr ends up a list of weakrefs
        # to types, it should be converted to the real types when
        # accessed again by the property getter.
        import weakref
        a = types.wsattr(int)
        a.datatype = [weakref.ref(int)]
        assert isinstance(a.datatype, list)
        assert a.datatype[0] is int

    def test_file_get_content_by_reading(self):
        class buffer:
            def read(self):
                return 'abcdef'
        f = types.File(file=buffer())
        assert f.content == 'abcdef'

    def test_file_content_overrides_file(self):
        class buffer:
            def read(self):
                return 'from-file'
        f = types.File(content='from-content', file=buffer())
        assert f.content == 'from-content'

    def test_file_setting_content_discards_file(self):
        class buffer:
            def read(self):
                return 'from-file'
        f = types.File(file=buffer())
        f.content = 'from-content'
        assert f.content == 'from-content'

    def test_file_field_storage(self):
        class buffer:
            def read(self):
                return 'from-file'

        class fieldstorage:
            filename = 'static.json'
            file = buffer()
            type = 'application/json'
        f = types.File(fieldstorage=fieldstorage)
        assert f.content == 'from-file'

    def test_file_field_storage_value(self):
        class buffer:
            def read(self):
                return 'from-file'

        class fieldstorage:
            filename = 'static.json'
            file = None
            type = 'application/json'
            value = 'from-value'
        f = types.File(fieldstorage=fieldstorage)
        assert f.content == 'from-value'

    def test_file_property_file(self):
        class buffer:
            def read(self):
                return 'from-file'
        buf = buffer()
        f = types.File(file=buf)
        assert f.file is buf

    def test_file_property_content(self):
        class buffer:
            def read(self):
                return 'from-file'
        f = types.File(content=six.b('from-content'))
        assert f.file.read() == six.b('from-content')
