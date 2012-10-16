# coding=utf-8

import unittest
import warnings
import datetime
import decimal
import sys
import six

from six import u, b

from webtest import TestApp

from wsme import WSRoot, Unset
from wsme import expose, validate
import wsme.types

warnings.filterwarnings('ignore', module='webob.dec')

binarysample = b('\x00\xff\x43')

try:
    1 / 0
except ZeroDivisionError:
    e = sys.exc_info()[1]
    zerodivisionerrormsg = str(e)


class CallException(RuntimeError):
    def __init__(self, faultcode, faultstring, debuginfo):
        self.faultcode = faultcode
        self.faultstring = faultstring
        self.debuginfo = debuginfo

    def __str__(self):
        return 'faultcode=%s, faultstring=%s, debuginfo=%s' % (
                self.faultcode, self.faultstring, self.debuginfo)


myenumtype = wsme.types.Enum(wsme.types.bytes, 'v1', 'v2')


class NestedInner(object):
    aint = int

    def __init__(self, aint=None):
        self.aint = aint


class NestedOuter(object):
    inner = NestedInner

    def __init__(self):
        self.inner = NestedInner(0)


class NamedAttrsObject(object):
    def __init__(self, v1=Unset, v2=Unset):
        self.attr_1 = v1
        self.attr_2 = v2

    attr_1 = wsme.types.wsattr(int, name='attr.1')
    attr_2 = wsme.types.wsattr(int, name='attr.2')


class NestedInnerApi(object):
    @expose(bool)
    def deepfunction(self):
        return True


class NestedOuterApi(object):
    inner = NestedInnerApi()


class ReturnTypes(object):
    @expose(wsme.types.bytes)
    def getbytes(self):
        return b("astring")

    @expose(wsme.types.text)
    def gettext(self):
        return u('\xe3\x81\xae')

    @expose(int)
    def getint(self):
        return 2

    @expose(float)
    def getfloat(self):
        return 3.14159265

    @expose(decimal.Decimal)
    def getdecimal(self):
        return decimal.Decimal('3.14159265')

    @expose(datetime.date)
    def getdate(self):
        return datetime.date(1994, 1, 26)

    @expose(datetime.time)
    def gettime(self):
        return datetime.time(12, 0, 0)

    @expose(datetime.datetime)
    def getdatetime(self):
        return datetime.datetime(1994, 1, 26, 12, 0, 0)

    @expose(wsme.types.binary)
    def getbinary(self):
        return binarysample

    @expose(NestedOuter)
    def getnested(self):
        n = NestedOuter()
        return n

    @expose([wsme.types.bytes])
    def getbytesarray(self):
        return [b("A"), b("B"), b("C")]

    @expose([NestedOuter])
    def getnestedarray(self):
        return [NestedOuter(), NestedOuter()]

    @expose({wsme.types.bytes: NestedOuter})
    def getnesteddict(self):
        return {b('a'): NestedOuter(), b('b'): NestedOuter()}

    @expose(myenumtype)
    def getenum(self):
        return b('v2')

    @expose(NamedAttrsObject)
    def getnamedattrsobj(self):
        return NamedAttrsObject(5, 6)


class ArgTypes(object):
    @expose(wsme.types.bytes)
    @validate(wsme.types.bytes)
    def setbytes(self, value):
        print(repr(value))
        assert type(value) == wsme.types.bytes
        return value

    @expose(wsme.types.text)
    @validate(wsme.types.text)
    def settext(self, value):
        print(repr(value))
        assert type(value) == wsme.types.text
        return value

    @expose(bool)
    @validate(bool)
    def setbool(self, value):
        print(repr(value))
        assert type(value) == bool
        return value

    @expose(int)
    @validate(int)
    def setint(self, value):
        print(repr(value))
        assert type(value) == int
        return value

    @expose(float)
    @validate(float)
    def setfloat(self, value):
        print(repr(value))
        assert type(value) == float
        return value

    @expose(decimal.Decimal)
    @validate(decimal.Decimal)
    def setdecimal(self, value):
        print(repr(value))
        assert type(value) == decimal.Decimal
        return value

    @expose(datetime.date)
    @validate(datetime.date)
    def setdate(self, value):
        print(repr(value))
        assert type(value) == datetime.date
        return value

    @expose(datetime.time)
    @validate(datetime.time)
    def settime(self, value):
        print(repr(value))
        assert type(value) == datetime.time
        return value

    @expose(datetime.datetime)
    @validate(datetime.datetime)
    def setdatetime(self, value):
        print(repr(value))
        assert type(value) == datetime.datetime
        return value

    @expose(wsme.types.binary)
    @validate(wsme.types.binary)
    def setbinary(self, value):
        print(repr(value))
        assert type(value) == six.binary_type
        return value

    @expose([wsme.types.bytes])
    @validate([wsme.types.bytes])
    def setbytesarray(self, value):
        print(repr(value))
        assert type(value) == list
        assert type(value[0]) == wsme.types.bytes, type(value[0])
        return value

    @expose([wsme.types.text])
    @validate([wsme.types.text])
    def settextarray(self, value):
        print(repr(value))
        assert type(value) == list
        assert type(value[0]) == wsme.types.text, type(value[0])
        return value

    @expose([datetime.datetime])
    @validate([datetime.datetime])
    def setdatetimearray(self, value):
        print(repr(value))
        assert type(value) == list
        assert type(value[0]) == datetime.datetime
        return value

    @expose(NestedOuter)
    @validate(NestedOuter)
    def setnested(self, value):
        print(repr(value))
        assert type(value) == NestedOuter
        return value

    @expose([NestedOuter])
    @validate([NestedOuter])
    def setnestedarray(self, value):
        print(repr(value))
        assert type(value) == list
        assert type(value[0]) == NestedOuter
        return value

    @expose({wsme.types.bytes: NestedOuter})
    @validate({wsme.types.bytes: NestedOuter})
    def setnesteddict(self, value):
        print(repr(value))
        assert type(value) == dict
        assert type(list(value.keys())[0]) == wsme.types.bytes
        assert type(list(value.values())[0]) == NestedOuter
        return value

    @expose(myenumtype)
    @validate(myenumtype)
    def setenum(self, value):
        print(value)
        assert type(value) == wsme.types.bytes
        return value

    @expose(NamedAttrsObject)
    @validate(NamedAttrsObject)
    def setnamedattrsobj(self, value):
        print(value)
        assert type(value) == NamedAttrsObject
        assert value.attr_1 == 10, value.attr_1
        assert value.attr_2 == 20, value.attr_2
        return value


class WithErrors(object):
    @expose()
    def divide_by_zero(self):
        1 / 0


class MiscFunctions(object):
    @expose(int)
    @validate(int, int)
    def multiply(self, a, b):
        return a * b


class WSTestRoot(WSRoot):
    argtypes = ArgTypes()
    returntypes = ReturnTypes()
    witherrors = WithErrors()
    nested = NestedOuterApi()
    misc = MiscFunctions()

    def reset(self):
        self._touched = False

    @expose()
    def touch(self):
        self._touched = True


class ProtocolTestCase(unittest.TestCase):
    protocol_options = {}

    def setUp(self):
        if self.__class__.__name__ != 'ProtocolTestCase':
            self.root = WSTestRoot()
            self.root.getapi()
            self.root.addprotocol(self.protocol, **self.protocol_options)

            self.app = TestApp(self.root.wsgiapp())

    def test_invalid_path(self):
        try:
            res = self.call('invalid_function')
            print(res)
            assert "No error raised"
        except CallException:
            e = sys.exc_info()[1]
            assert e.faultcode == 'Client'
            assert e.faultstring.lower() == \
                    u('unknown function name: invalid_function')

    def test_serverside_error(self):
        try:
            res = self.call('witherrors/divide_by_zero')
            print(res)
            assert "No error raised"
        except CallException:
            e = sys.exc_info()[1]
            print(e)
            assert e.faultcode == 'Server'
            assert e.faultstring == zerodivisionerrormsg
            assert e.debuginfo is not None

    def test_serverside_error_nodebug(self):
        self.root._debug = False
        try:
            res = self.call('witherrors/divide_by_zero')
            print(res)
            assert "No error raised"
        except CallException:
            e = sys.exc_info()[1]
            print(e)
            assert e.faultcode == 'Server'
            assert e.faultstring == zerodivisionerrormsg
            assert e.debuginfo is None

    def test_touch(self):
        r = self.call('touch')
        assert r is None, r

    def test_return_bytes(self):
        r = self.call('returntypes/getbytes', _rt=wsme.types.bytes)
        assert r == b('astring'), r

    def test_return_text(self):
        r = self.call('returntypes/gettext', _rt=wsme.types.text)
        assert r == u('\xe3\x81\xae'), r

    def test_return_int(self):
        r = self.call('returntypes/getint')
        assert r == 2 or r == '2', r

    def test_return_float(self):
        r = self.call('returntypes/getfloat')
        assert r == 3.14159265 or r == '3.14159265', r

    def test_return_decimal(self):
        r = self.call('returntypes/getdecimal')
        assert r in (decimal.Decimal('3.14159265'), '3.14159265'), r

    def test_return_date(self):
        r = self.call('returntypes/getdate')
        assert r == datetime.date(1994, 1, 26) or r == '1994-01-26', r

    def test_return_time(self):
        r = self.call('returntypes/gettime')
        assert r == datetime.time(12) or r == '12:00:00', r

    def test_return_datetime(self):
        r = self.call('returntypes/getdatetime')
        assert r == datetime.datetime(1994, 1, 26, 12) \
            or r == '1994-01-26T12:00:00', r

    def test_return_binary(self):
        r = self.call('returntypes/getbinary', _rt=wsme.types.binary)
        assert r == binarysample, r

    def test_return_nested(self):
        r = self.call('returntypes/getnested', _rt=NestedOuter)
        assert r == {'inner': {'aint': 0}}, r

    def test_return_bytesarray(self):
        r = self.call('returntypes/getbytesarray', _rt=[six.binary_type])
        assert r == [b('A'), b('B'), b('C')], r

    def test_return_nestedarray(self):
        r = self.call('returntypes/getnestedarray', _rt=[NestedOuter])
        assert r == [{'inner': {'aint': 0}}, {'inner': {'aint': 0}}], r

    def test_return_nesteddict(self):
        r = self.call('returntypes/getnesteddict',
            _rt={wsme.types.bytes: NestedOuter})
        assert r == {
            b('a'): {'inner': {'aint': 0}},
            b('b'): {'inner': {'aint': 0}}}, r

    def test_return_enum(self):
        r = self.call('returntypes/getenum', _rt=myenumtype)
        assert r == b('v2'), r

    def test_return_namedattrsobj(self):
        r = self.call('returntypes/getnamedattrsobj', _rt=NamedAttrsObject)
        assert r == {'attr.1': 5, 'attr.2': 6}

    def test_setbytes(self):
        assert self.call('argtypes/setbytes', value=b('astring'),
            _rt=wsme.types.bytes) == b('astring')

    def test_settext(self):
        assert self.call('argtypes/settext', value=u('\xe3\x81\xae'),
                        _rt=wsme.types.text) == u('\xe3\x81\xae')

    def test_setint(self):
        r = self.call('argtypes/setint', value=3, _rt=int)
        assert r == 3, r

    def test_setfloat(self):
        assert self.call('argtypes/setfloat', value=3.54,
                         _rt=float) == 3.54

    def test_setdecimal(self):
        value = decimal.Decimal('3.14')
        assert self.call('argtypes/setdecimal', value=value,
                         _rt=decimal.Decimal) == value

    def test_setdate(self):
        value = datetime.date(2008, 4, 6)
        r = self.call('argtypes/setdate', value=value,
                      _rt=datetime.date)
        assert r == value

    def test_settime(self):
        value = datetime.time(12, 12, 15)
        r = self.call('argtypes/settime', value=value,
                      _rt=datetime.time)
        assert r == datetime.time(12, 12, 15)

    def test_setdatetime(self):
        value = datetime.datetime(2008, 4, 6, 12, 12, 15)
        r = self.call('argtypes/setdatetime', value=value,
                      _rt=datetime.datetime)
        assert r == datetime.datetime(2008, 4, 6, 12, 12, 15)

    def test_setbinary(self):
        value = binarysample
        r = self.call('argtypes/setbinary', value=(value, wsme.types.binary),
                    _rt=wsme.types.binary) == value
        print(r)

    def test_setnested(self):
        value = {'inner': {'aint': 54}}
        r = self.call('argtypes/setnested',
                         value=(value, NestedOuter),
                         _rt=NestedOuter)
        assert r == value

    def test_setbytesarray(self):
        value = [b("1"), b("2"), b("three")]
        r = self.call('argtypes/setbytesarray',
                         value=(value, [wsme.types.bytes]),
                         _rt=[wsme.types.bytes])
        assert r == value, r

    def test_settextarray(self):
        value = [u("1")]
        r = self.call('argtypes/settextarray',
                         value=(value, [wsme.types.text]),
                         _rt=[wsme.types.text])
        assert r == value, r

    def test_setdatetimearray(self):
        value = [
            datetime.datetime(2008, 3, 6, 12, 12, 15),
            datetime.datetime(2008, 4, 6, 2, 12, 15),
        ]
        r = self.call('argtypes/setdatetimearray',
                         value=(value, [datetime.datetime]),
                         _rt=[datetime.datetime])
        assert r == value

    def test_setnestedarray(self):
        value = [
            {'inner': {'aint': 54}},
            {'inner': {'aint': 55}},
        ]
        r = self.call('argtypes/setnestedarray',
                         value=(value, [NestedOuter]),
                         _rt=[NestedOuter])
        assert r == value

    def test_setnesteddict(self):
        value = {
            b('o1'): {'inner': {'aint': 54}},
            b('o2'): {'inner': {'aint': 55}},
        }
        r = self.call('argtypes/setnesteddict',
                        value=(value, {six.binary_type: NestedOuter}),
                        _rt={six.binary_type: NestedOuter})
        print(r)
        assert r == value

    def test_setenum(self):
        value = b('v1')
        r = self.call('argtypes/setenum', value=value,
                      _rt=myenumtype)
        assert r == value

    def test_setnamedattrsobj(self):
        value = {'attr.1': 10, 'attr.2': 20}
        r = self.call('argtypes/setnamedattrsobj',
            value=(value, NamedAttrsObject),
            _rt=NamedAttrsObject)
        assert r == value

    def test_nested_api(self):
        r = self.call('nested/inner/deepfunction', _rt=bool)
        assert r is True

    def test_missing_argument(self):
        try:
            r = self.call('argtypes/setdatetime')
            print(r)
            assert "No error raised"
        except CallException:
            e = sys.exc_info()[1]
            print(e)
            assert e.faultcode == 'Client'
            assert e.faultstring == u('Missing argument: "value"')

    def test_misc_multiply(self):
        assert self.call('misc/multiply', a=5, b=2, _rt=int) == 10

    def test_html_format(self):
        res = self.call('argtypes/setdatetime', _accept="text/html",
            _no_result_decode=True)
        assert res.content_type == 'text/html', res.content_type
