# coding=utf-8

import unittest
import warnings
import datetime
import decimal
import base64

from webob.dec import wsgify
from webtest import TestApp

from wsme import *
import wsme.types

warnings.filterwarnings('ignore', module='webob.dec')

binarysample = r'\x00\xff\x43'


class CallException(RuntimeError):
    def __init__(self, faultcode, faultstring, debuginfo):
        self.faultcode = faultcode
        self.faultstring = faultstring
        self.debuginfo = debuginfo

    def __str__(self):
        return 'faultcode=%s, faultstring=%s, debuginfo=%s' % (
                self.faultcode, self.faultstring, self.debuginfo)


class NestedInner(object):
    aint = int

    def __init__(self, aint=None):
        self.aint = aint


class NestedOuter(object):
    inner = NestedInner

    def __init__(self):
        self.inner = NestedInner(0)


class ReturnTypes(object):
    @expose(str)
    def getstr(self):
        return "astring"

    @expose(unicode)
    def getunicode(self):
        return u"の"

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


class ArgTypes(object):
    @expose(str)
    @validate(str)
    def setstr(self, value):
        print repr(value)
        assert type(value) == str
        return value

    @expose(unicode)
    @validate(unicode)
    def setunicode(self, value):
        print repr(value)
        assert type(value) == unicode
        return value

    @expose(bool)
    @validate(bool)
    def setbool(self, value):
        print repr(value)
        assert type(value) == bool
        return value
    
    @expose(int)
    @validate(int)
    def setint(self, value):
        print repr(value)
        assert type(value) == int
        return value

    @expose(float)
    @validate(float)
    def setfloat(self, value):
        print repr(value)
        assert type(value) == float
        return value

    @expose(decimal.Decimal)
    @validate(decimal.Decimal)
    def setdecimal(self, value):
        print repr(value)
        assert type(value) == decimal.Decimal
        return value

    @expose(datetime.date)
    @validate(datetime.date)
    def setdate(self, value):
        print repr(value)
        assert type(value) == datetime.date
        return value

    @expose(datetime.time)
    @validate(datetime.time)
    def settime(self, value):
        print repr(value)
        assert type(value) == datetime.time
        return value

    @expose(datetime.datetime)
    @validate(datetime.datetime)
    def setdatetime(self, value):
        print repr(value)
        assert type(value) == datetime.datetime
        return value

    @expose(wsme.types.binary)
    @validate(wsme.types.binary)
    def setbinary(self, value):
        print repr(value)
        assert type(value) == str
        return value

    @expose(NestedOuter)
    @validate(NestedOuter)
    def setnested(self, value):
        print repr(value)
        assert type(value) == NestedOuter
        return value


class WithErrors(object):
    @expose()
    def divide_by_zero(self):
        1 / 0


class WSTestRoot(WSRoot):
    argtypes = ArgTypes()
    returntypes = ReturnTypes()
    witherrors = WithErrors()

    def reset(self):
        self.touched = False

    @expose()
    def touch(self):
        self.touched = True


class ProtocolTestCase(unittest.TestCase):
    def setUp(self):
        if self.__class__.__name__ != 'ProtocolTestCase':
            self.root = WSTestRoot([self.protocol])

            self.app = TestApp(wsgify(self.root._handle_request))

    def test_invalid_path(self):
        try:
            res = self.call('invalid_function')
            assert "No error raised"
        except CallException, e:
            assert e.faultcode == 'Client'
            assert e.faultstring == u'Unknown function name: invalid_function'

    def test_serverside_error(self):
        try:
            res = self.call('witherrors/divide_by_zero')
            assert "No error raised"
        except CallException, e:
            print e
            assert e.faultcode == 'Server'
            assert e.faultstring == u'integer division or modulo by zero'

    def test_touch(self):
        assert self.call('touch') is None

    def test_return_str(self):
        r = self.call('returntypes/getstr')
        assert r == 'astring', r

    def test_return_unicode(self):
        r = self.call('returntypes/getunicode')
        assert r == u'の', r

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
        r = self.call('returntypes/getbinary')
        assert r == binarysample or r == base64.encodestring(binarysample), r

    def test_return_nested(self):
        r = self.call('returntypes/getnested')
        assert r == {'inner': {'aint': 0}} or r == {'inner': {'aint': '0'}}, r

    def test_setstr(self):
        assert self.call('argtypes/setstr', value='astring') in ('astring',)

    def test_setunicode(self):
        assert self.call('argtypes/setunicode', value=u'の') in (u'の',)

    def test_setint(self):
        assert self.call('argtypes/setint', value=3) in (3, '3')

    def test_setfloat(self):
        return self.call('argtypes/setfloat', value=3.54) in (3.54, '3.54')

    def test_setdecimal(self):
        return self.call('argtypes/setdecimal', value='3.14') in ('3.14', decimal.Decimal('3.14'))

    def test_setdate(self):
        return self.call('argtypes/setdate', value='2008-04-06') in (
                datetime.date(2008, 4, 6), '2008-04-06')

    def test_settime(self):
        return self.call('argtypes/settime', value='12:12:15') \
                in ('12:12:15', datetime.time(12, 12, 15))

    def test_setdatetime(self):
        return self.call('argtypes/setdatetime', value='2008-04-06T12:12:15') \
                in ('2008-04-06T12:12:15',
                    datetime.datetime(2008, 4, 6, 12, 12, 15))

    def test_setbinary(self):
        r = self.call('argtypes/setbinary',
                value=base64.encodestring(binarysample))
        assert r == binarysample or r == base64.encodestring(binarysample), r

    def test_setnested(self):
        return self.call('argtypes/setnested',
            value={'inner': {'aint': 54}}) in (
                {'inner': {'aint': 54}},
                {'inner': {'aint': '54'}}
            )
