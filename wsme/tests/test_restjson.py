import decimal
import base64

import wsme.tests.protocol
try:
    import simplejson as json
except:
    import json

import wsme.restjson
from wsme.utils import *

def prepare_value(value, datatype):
    if datatype in (datetime.date, datetime.time, datetime.datetime):
        return value.isoformat()
    if datatype == decimal.Decimal:
        return str(value)
    if datatype == wsme.types.binary:
        return base64.encodestring(value)
    return value

def prepare_result(value, datatype):
    if datatype == datetime.date:
        return parse_isodate(value)
    if datatype == datetime.time:
        return parse_isotime(value)
    if datatype == datetime.datetime:
        return parse_isodatetime(value)
    if hasattr(datatype, '_wsme_attributes'):
        for name, attr in datatype._wsme_attributes:
            if name not in value:
                continue
            value[name] = prepare_result(value[name], attr.datatype)
        return value
    if datatype == wsme.types.binary:
        return base64.decodestring(value)
    if type(value) != datatype:
        return datatype(value)
    return value

class TestRestJson(wsme.tests.protocol.ProtocolTestCase):
    protocol = 'REST+Json'

    def call(self, fpath, _rt=None, **kw):
        for key in kw:
            if isinstance(kw[key], tuple):
                value, datatype = kw[key]
            else:
                value = kw[key]
                datatype = type(value)
            kw[key] = prepare_value(value, datatype)
        content = json.dumps(kw)
        res = self.app.post(
            '/' + fpath,
            content,
            headers={
                'Content-Type': 'application/json',
            },
            expect_errors=True)
        print "Received:", res.body
        r = json.loads(res.body)
        if 'result' in r:
            r = r['result']
            if _rt and r:
                r = prepare_result(r, _rt)
            return r
        else:
            raise wsme.tests.protocol.CallException(
                    r['faultcode'],
                    r['faultstring'],
                    r.get('debuginfo'))

        return json.loads(res.body)
