# coding=utf-8

import unittest
import warnings
import datetime
import decimal

from webob.dec import wsgify
from webtest import TestApp

from wsme import *

warnings.filterwarnings('ignore', module='webob.dec')


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

    @expose(NestedOuter)
    def getnested(self):
        n = NestedOuter()
        return n


class WithErrors(object):
    @expose()
    def divide_by_zero(self):
        1 / 0


class WSTestRoot(WSRoot):
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

    def test_return_nested(self):
        r = self.call('returntypes/getnested')
        assert r == {'inner': {'aint': 0}} or r == {'inner': {'aint': '0'}}, r
