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
        el(obj)
    elif type(obj) in (int, float, decimal.Decimal):
        el(str(obj))
    elif type(obj) in (datetime.date, datetime.time, datetime.datetime):
        el(obj.isoformat())
    elif type(obj) == dict:
        for key, obj in obj.items():
            e.append(dumpxml(key, obj))
    return el

class TestRestJson(wsme.tests.protocol.ProtocolTestCase):
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
                    el.find('debuginfo') and 
                        el.find('debuginfo').text or None)

        else:
            pass
        return xml.loads(res.body)

