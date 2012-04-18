import base64
import datetime
import decimal
import urllib

import wsme.tests.protocol

try:
    import simplejson as json
except:
    import json

import wsme.protocols.restjson
from wsme.protocols.restjson import fromjson, tojson
from wsme.utils import parse_isodatetime, parse_isotime, parse_isodate
from wsme.types import isusertype, register_type


def prepare_value(value, datatype):
    if isinstance(datatype, list):
        return [prepare_value(item, datatype[0]) for item in value]
    if isinstance(datatype, dict):
        return dict((
            (prepare_value(item[0], datatype.keys()[0]),
                prepare_value(item[1], datatype.values()[0]))
            for item in value.items()
        ))
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
    if isinstance(datatype, dict):
        return dict((
            (prepare_result(item[0], datatype.keys()[0]),
                prepare_result(item[1], datatype.values()[0]))
            for item in value.items()
        ))
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

    def test_form_urlencoded_args(self):
        params = {
            'value[0].inner.aint': 54,
            'value[1].inner.aint': 55
        }
        body = urllib.urlencode(params)
        r = self.app.post('/argtypes/setnestedarray.json', body,
            headers={'Content-Type': 'application/x-www-form-urlencoded'})
        print r

        assert json.loads(r.body) == [
            {'inner': {'aint': 54}},
            {'inner': {'aint': 55}}]

    def test_body_and_params(self):
        r = self.app.post('/argtypes/setint.json?value=2',
                '{"value": 2}',
                headers={"Content-Type": "application/json"},
                expect_errors=True)
        print r
        assert r.status_int == 400
        assert json.loads(r.body)['faultstring'] == \
            "Cannot read parameters from both a body and GET/POST params"

    def test_inline_body(self):
        params = urllib.urlencode({'body': '{"value": 4}'})
        r = self.app.get('/argtypes/setint.json?' + params)
        print r
        assert json.loads(r.body) == 4

    def test_empty_body(self):
        params = urllib.urlencode({'body': ''})
        r = self.app.get('/returntypes/getint.json?' + params)
        print r
        assert json.loads(r.body) == 2

    def test_unknown_arg(self):
        r = self.app.post('/returntypes/getint.json',
            '{"a": 2}',
            headers={"Content-Type": "application/json"},
            expect_errors=True)
        print r
        assert r.status_int == 400
        assert json.loads(r.body)['faultstring'].startswith(
                "Unknown argument:")

        r = self.app.get('/returntypes/getint.json?a=2',
            expect_errors=True)
        print r
        assert r.status_int == 400
        assert json.loads(r.body)['faultstring'].startswith(
                "Unknown argument:")

    def test_array_tojson(self):
        assert tojson([int], None) is None
        assert tojson([int], []) == []
        assert tojson([str], ['1', '4']) == ['1', '4']

    def test_dict_tojson(self):
        assert tojson({int: str}, None) is None
        assert tojson({int: str}, {5: '5'}) == {5: '5'}

    def test_None_tojson(self):
        for dt in (datetime.date, datetime.time, datetime.datetime,
                decimal.Decimal):
            assert tojson(dt, None) is None

    def test_None_fromjson(self):
        for dt in (str, int,
                datetime.date, datetime.time, datetime.datetime,
                decimal.Decimal,
                [int], {int: int}):
            assert fromjson(dt, None) is None

    def test_parse_arg(self):
        assert self.root.protocols[0].parse_arg('a', '5') == 5

    def test_nest_result(self):
        self.root.protocols[0].nest_result = True
        r = self.app.get('/returntypes/getint.json')
        print r
        assert json.loads(r.body) == {"result": 2}

    def test_encode_sample_value(self):
        class MyType(object):
            aint = int
            astr = str

        register_type(MyType)

        v = MyType()
        v.aint = 4
        v.astr = 's'

        r = self.root.protocols[0].encode_sample_value(MyType, v, True)
        print r
        assert r[0] == ('javascript')
        assert r[1] == json.dumps({'aint': 4, 'astr': 's'},
            ensure_ascii=False, indent=4, sort_keys=True)
