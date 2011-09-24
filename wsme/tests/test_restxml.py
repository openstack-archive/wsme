import decimal
import datetime
import base64

import wsme.tests.protocol
from wsme.utils import *

try:
    import xml.etree.ElementTree as et
except:
    import cElementTree as et

import wsme.restxml


def dumpxml(key, obj, datatype=None):
    el = et.Element(key)
    if isinstance(obj, tuple):
        obj, datatype = obj
    if datatype == wsme.types.binary:
        el.text = base64.encodestring(obj)
    elif isinstance(obj, basestring):
        el.text = obj
    elif type(obj) in (int, float, decimal.Decimal):
        el.text = str(obj)
    elif type(obj) in (datetime.date, datetime.time, datetime.datetime):
        el.text = obj.isoformat()
    elif hasattr(datatype, '_wsme_attributes'):
        for name, attr in datatype._wsme_attributes:
            if name not in obj:
                continue
            o = obj[name]
            el.append(dumpxml(name, o, attr.datatype))
    elif type(obj) == dict:
        for name, value in obj.items():
            el.append(dumpxml(name, value))
    return el


def loadxml(el, datatype):
    print el, datatype, len(el)
    if len(el):
        d = {}
        for name, attr in datatype._wsme_attributes:
            child = el.find(name)
            print name, attr, child
            if child is not None:
                d[name] = loadxml(child, attr.datatype)
        print d
        return d
    else:
        if datatype == datetime.date:
            return parse_isodate(el.text)
        if datatype == datetime.time:
            return parse_isotime(el.text)
        if datatype == datetime.datetime:
            return parse_isodatetime(el.text)
        if datatype == wsme.types.binary:
            return base64.decodestring(el.text)
        if datatype is None:
            return el.text
        return datatype(el.text)


class TestRestXML(wsme.tests.protocol.ProtocolTestCase):
    protocol = 'REST+XML'

    def call(self, fpath, _rt=None, **kw):
        el = dumpxml('parameters', kw)
        content = et.tostring(el)
        res = self.app.post(
            '/' + fpath,
            content,
            headers={
                'Content-Type': 'text/xml',
            },
            expect_errors=True)
        print "Received:", res.body
        el = et.fromstring(res.body)
        if el.tag == 'error':
            raise wsme.tests.protocol.CallException(
                    el.find('faultcode').text,
                    el.find('faultstring').text,
                    el.find('debuginfo') is not None and
                        el.find('debuginfo').text or None)

        else:
            return loadxml(et.fromstring(res.body), _rt)
