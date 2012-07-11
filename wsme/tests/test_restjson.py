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
from wsme.api import expose, validate


import six
from six import b, u

if six.PY3:
    from urllib.parse import urlencode
else:
    from urllib import urlencode


def prepare_value(value, datatype):
    if isinstance(datatype, list):
        return [prepare_value(item, datatype[0]) for item in value]
    if isinstance(datatype, dict):
        key_type, value_type = list(datatype.items())[0]
        return dict((
            (prepare_value(item[0], key_type),
                prepare_value(item[1], value_type))
            for item in value.items()
        ))
    if datatype in (datetime.date, datetime.time, datetime.datetime):
        return value.isoformat()
    if datatype == decimal.Decimal:
        return str(value)
    if datatype == wsme.types.binary:
        return base64.encodestring(value).decode('ascii')
    if datatype == wsme.types.bytes:
        return value.decode('ascii')
    return value


def prepare_result(value, datatype):
    print(value, datatype)
    if datatype == wsme.types.binary:
        return base64.decodestring(value.encode('ascii'))
    if isusertype(datatype):
        datatype = datatype.basetype
    if isinstance(datatype, list):
        return [prepare_result(item, datatype[0]) for item in value]
    if isinstance(datatype, dict):
        return dict((
            (prepare_result(item[0], list(datatype.keys())[0]),
                prepare_result(item[1], list(datatype.values())[0]))
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
    if datatype == wsme.types.bytes:
        return value.encode('ascii')
    if type(value) != datatype:
        return datatype(value)
    return value


class Obj(wsme.types.Base):
    id = int
    name = wsme.types.text


class CRUDResult(object):
    data = Obj
    message = wsme.types.text

    def __init__(self, data=wsme.types.Unset, message=wsme.types.Unset):
        self.data = data
        self.message = message


class MiniCrud(object):
    @expose(CRUDResult, method='PUT')
    @validate(Obj)
    def create(self, data):
        print(repr(data))
        return CRUDResult(data, u('create'))

    @expose(CRUDResult, method='GET')
    @validate(Obj)
    def read(self, ref):
        print(repr(ref))
        if ref.id == 1:
            ref.name = u('test')
        return CRUDResult(ref, u('read'))

    @expose(CRUDResult, method='POST')
    @validate(Obj)
    def update(self, data):
        print(repr(data))
        return CRUDResult(data, u('update'))

    @expose(CRUDResult, method='DELETE')
    @validate(Obj)
    def delete(self, ref):
        print(repr(ref))
        if ref.id == 1:
            ref.name = u('test')
        return CRUDResult(ref, u('delete'))

wsme.tests.protocol.WSTestRoot.crud = MiniCrud()


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
        print("Received:", res.body)

        if _no_result_decode:
            return res

        r = json.loads(res.text)
        if res.status_int == 200:
            if _rt and r:
                r = prepare_result(r, _rt)
            return r
        else:
            raise wsme.tests.protocol.CallException(
                    r['faultcode'],
                    r['faultstring'],
                    r.get('debuginfo'))

        return json.loads(res.text)

    def test_fromjson(self):
        assert fromjson(str, None) == None

    def test_keyargs(self):
        r = self.app.get('/argtypes/setint.json?value=2')
        print(r)
        assert json.loads(r.text) == 2

        nestedarray = 'value[0].inner.aint=54&value[1].inner.aint=55'
        r = self.app.get('/argtypes/setnestedarray.json?' + nestedarray)
        print(r)
        assert json.loads(r.text) == [
            {'inner': {'aint': 54}},
            {'inner': {'aint': 55}}]

    def test_form_urlencoded_args(self):
        params = {
            'value[0].inner.aint': 54,
            'value[1].inner.aint': 55
        }
        body = urlencode(params)
        r = self.app.post('/argtypes/setnestedarray.json', body,
            headers={'Content-Type': 'application/x-www-form-urlencoded'})
        print(r)

        assert json.loads(r.text) == [
            {'inner': {'aint': 54}},
            {'inner': {'aint': 55}}]

    def test_body_and_params(self):
        r = self.app.post('/argtypes/setint.json?value=2',
                '{"value": 2}',
                headers={"Content-Type": "application/json"},
                expect_errors=True)
        print(r)
        assert r.status_int == 400
        assert json.loads(r.text)['faultstring'] == \
            "Cannot read parameters from both a body and GET/POST params"

    def test_inline_body(self):
        params = urlencode({'body': '{"value": 4}'})
        r = self.app.get('/argtypes/setint.json?' + params)
        print(r)
        assert json.loads(r.text) == 4

    def test_empty_body(self):
        params = urlencode({'body': ''})
        r = self.app.get('/returntypes/getint.json?' + params)
        print(r)
        assert json.loads(r.text) == 2

    def test_unknown_arg(self):
        r = self.app.post('/returntypes/getint.json',
            '{"a": 2}',
            headers={"Content-Type": "application/json"},
            expect_errors=True)
        print(r)
        assert r.status_int == 400
        assert json.loads(r.text)['faultstring'].startswith(
                "Unknown argument:")

        r = self.app.get('/returntypes/getint.json?a=2',
            expect_errors=True)
        print(r)
        assert r.status_int == 400
        assert json.loads(r.text)['faultstring'].startswith(
                "Unknown argument:")

    def test_unset_attrs(self):
        class AType(object):
            attr = int

        wsme.types.register_type(AType)

        j = tojson(AType, AType())
        assert j == {}

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
        print(r)
        assert json.loads(r.text) == {"result": 2}

    def test_encode_sample_value(self):
        class MyType(object):
            aint = int
            astr = str

        register_type(MyType)

        v = MyType()
        v.aint = 4
        v.astr = 's'

        r = self.root.protocols[0].encode_sample_value(MyType, v, True)
        print(r)
        assert r[0] == ('javascript')
        assert r[1] == json.dumps({'aint': 4, 'astr': 's'},
            ensure_ascii=False, indent=4, sort_keys=True)

    def test_bytes_tojson(self):
        assert tojson(wsme.types.bytes, None) is None
        assert tojson(wsme.types.bytes, b('ascii')) == u('ascii')

    def test_encode_sample_params(self):
        r = self.root.protocols[0].encode_sample_params(
            [('a', int, 2)], True
        )
        assert r[0] == 'javascript', r[0]
        assert r[1] == '''{
    "a": 2
}''', r[1]

    def test_encode_sample_result(self):
        r = self.root.protocols[0].encode_sample_result(
            int, 2, True
        )
        assert r[0] == 'javascript', r[0]
        assert r[1] == '''2'''
        self.root.protocols[0].nest_result = True
        r = self.root.protocols[0].encode_sample_result(
            int, 2, True
        )
        assert r[0] == 'javascript', r[0]
        assert r[1] == '''{
    "result": 2
}'''

    def test_PUT(self):
        data = {"id": 1, "name": u("test")}
        content = json.dumps(dict(data=data))
        headers = {
            'Content-Type': 'application/json',
        }
        res = self.app.put(
            '/crud',
            content,
            headers=headers,
            expect_errors=False)
        print("Received:", res.body)
        result = json.loads(res.text)
        print(result)
        assert result['data']['id'] == 1
        assert result['data']['name'] == u("test")
        assert result['message'] == "create"

    def test_GET(self):
        headers = {
            'Content-Type': 'application/json',
        }
        res = self.app.get(
            '/crud?ref.id=1',
            headers=headers,
            expect_errors=False)
        print("Received:", res.body)
        result = json.loads(res.text)
        print(result)
        assert result['data']['id'] == 1
        assert result['data']['name'] == u("test")
        assert result['message'] == "read"

    def test_POST(self):
        headers = {
            'Content-Type': 'application/json',
        }
        res = self.app.post(
            '/crud',
            json.dumps(dict(data=dict(id=1, name=u('test')))),
            headers=headers,
            expect_errors=False)
        print("Received:", res.body)
        result = json.loads(res.text)
        print(result)
        assert result['data']['id'] == 1
        assert result['data']['name'] == u("test")
        assert result['message'] == "update"

    def test_DELETE(self):
        res = self.app.delete(
            '/crud.json?ref.id=1',
            expect_errors=False)
        print("Received:", res.body)
        result = json.loads(res.text)
        print(result)
        assert result['data']['id'] == 1
        assert result['data']['name'] == u("test")
        assert result['message'] == "delete"
