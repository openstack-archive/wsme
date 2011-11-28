import decimal
import base64
import datetime

import wsme.tests.protocol

try:
    import simplejson as json
except:
    import json

import wsme.protocols.restjson
from wsme.protocols.restjson import fromjson
from wsme.utils import parse_isodatetime, parse_isotime, parse_isodate
from wsme.types import isusertype


def prepare_value(value, datatype):
    if isinstance(datatype, list):
        return [prepare_value(item, datatype[0]) for item in value]
    if datatype in (datetime.date, datetime.time, datetime.datetime):
        return value.isoformat()
    if datatype == decimal.Decimal:
        return str(value)
    if datatype == wsme.types.binary:
        return base64.encodestring(value)
    return value


def prepare_result(value, datatype):
    if isusertype(datatype):
        datatype = datatype.basetype
    if isinstance(datatype, list):
        return [prepare_result(item, datatype[0]) for item in value]
    if datatype == datetime.date:
        return parse_isodate(value)
    if datatype == datetime.time:
        return parse_isotime(value)
    if datatype == datetime.datetime:
        return parse_isodatetime(value)
    if hasattr(datatype, '_wsme_attributes'):
        for attr in datatype._wsme_attributes:
            if attr.key not in value:
                continue
            value[attr.key] = prepare_result(value[attr.key], attr.datatype)
        return value
    if datatype == wsme.types.binary:
        return base64.decodestring(value)
    if type(value) != datatype:
        return datatype(value)
    return value


class TestRestJson(wsme.tests.protocol.ProtocolTestCase):
    protocol = 'restjson'

    def call(self, fpath, _rt=None, _accept=None,
                _no_result_decode=False, **kw):
        for key in kw:
            if isinstance(kw[key], tuple):
                value, datatype = kw[key]
            else:
                value = kw[key]
                datatype = type(value)
            kw[key] = prepare_value(value, datatype)
        content = json.dumps(kw)
        headers = {
            'Content-Type': 'application/json',
        }
        if _accept is not None:
            headers["Accept"] = _accept
        res = self.app.post(
            '/' + fpath,
            content,
            headers=headers,
            expect_errors=True)
        print "Received:", res.body

        if _no_result_decode:
            return res

        r = json.loads(res.body)
        if res.status_int == 200:
            if _rt and r:
                r = prepare_result(r, _rt)
            return r
        else:
            raise wsme.tests.protocol.CallException(
                    r['faultcode'],
                    r['faultstring'],
                    r.get('debuginfo'))

        return json.loads(res.body)

    def test_fromjson(self):
        assert fromjson(str, None) == None

    def test_keyargs(self):
        r = self.app.get('/argtypes/setint.json?value=2')
        print r
        assert json.loads(r.body) == 2

        nestedarray = 'value[0].inner.aint=54&value[1].inner.aint=55'
        r = self.app.get('/argtypes/setnestedarray.json?' + nestedarray)
        print r
        assert json.loads(r.body) == [
            {'inner': {'aint': 54}},
            {'inner': {'aint': 55}}]
