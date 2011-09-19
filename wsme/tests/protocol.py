# coding=utf-8

import unittest
import warnings
import datetime
import decimal

from webob.dec import wsgify
from webtest import TestApp

from wsme import *

warnings.filterwarnings('ignore', module='webob.dec')


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
    def getdate(self):
        return datetime.time(12, 0, 0)

    @expose(datetime.datetime)
    def getdate(self):
        return datetime.datetime(1994, 1, 26, 12, 0, 0)

class WSTestRoot(WSRoot):
    returntypes = ReturnTypes()

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

    def _call(self, fpath, **kw):
        pass
    
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
        assert r == 2, r

    def test_return_float(self):
        r = self.call('returntypes/getfloat')
        assert r == 3.14159265, r

