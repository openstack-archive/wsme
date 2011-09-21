import decimal
import datetime

import wsme.tests.protocol

try:
    import xml.etree.ElementTree as et
except:
    import cElementTree as et

import wsme.restxml


def dumpxml(key, obj):
    el = et.Element(key)
    if isinstance(obj, basestring):
        el.text = obj
    elif type(obj) in (int, float, decimal.Decimal):
        el.text = str(obj)
    elif type(obj) in (datetime.date, datetime.time, datetime.datetime):
        el.text = obj.isoformat()
    elif type(obj) == dict:
        for key, obj in obj.items():
            el.append(dumpxml(key, obj))
    return el


def loadxml(el):
    if len(el):
        d = {}
        for child in el:
            d[child.tag] = loadxml(child)
        return d
    else:
        return el.text


class TestRestXML(wsme.tests.protocol.ProtocolTestCase):
    protocol = 'REST+XML'

    def call(self, fpath, **kw):
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
            return loadxml(et.fromstring(res.body))
