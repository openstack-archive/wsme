from __future__ import print_function

import unittest
from flask import Flask, json, abort
import six
from wsmeext.flask import signature
from wsme.api import Response
from wsme.types import Base, text


class Model(Base):
    id = int
    name = text


class Criterion(Base):
    op = text
    attr = text
    value = text

test_app = Flask(__name__)


@test_app.route('/multiply')
@signature(int, int, int)
def multiply(a, b):
    return a * b


@test_app.route('/divide_by_zero')
@signature(None)
def divide_by_zero():
    return 1 / 0


@test_app.route('/models')
@signature([Model], [Criterion])
def list_models(q=None):
    if q:
        name = q[0].value
    else:
        name = 'first'
    return [Model(name=name)]


@test_app.route('/models/<name>')
@signature(Model, text)
def get_model(name):
    return Model(name=name)


@test_app.route('/models/<name>/secret')
@signature(Model, text)
def model_secret(name):
    abort(403)


@test_app.route('/models/<name>/custom-error')
@signature(Model, text)
def model_custom_error(name):
    class CustomError(Exception):
        code = 412
    raise CustomError("FOO!")


@test_app.route('/models', methods=['POST'])
@signature(Model, body=Model)
def post_model(body):
    return Model(name=body.name)


@test_app.route('/status_sig')
@signature(int, status_code=201)
def get_status_sig():
    return 1


@test_app.route('/status_response')
@signature(int)
def get_status_response():
    return Response(1, status_code=201)


class FlaskrTestCase(unittest.TestCase):

    def setUp(self):
        test_app.config['TESTING'] = True
        self.app = test_app.test_client()

    def tearDown(self):
        pass

    def test_multiply(self):
        r = self.app.get('/multiply?a=2&b=5')
        assert r.data == six.b('10')

    def test_get_model(self):
        resp = self.app.get('/models/test')
        assert resp.status_code == 200

    def test_list_models(self):
        resp = self.app.get('/models')
        assert resp.status_code == 200

    def test_array_parameter(self):
        resp = self.app.get('/models?q.op=%3D&q.attr=name&q.value=second')
        assert resp.status_code == 200
        print(resp.data)
        self.assertEquals(
            resp.data, six.b('[{"name": "second"}]')
        )

    def test_post_model(self):
        resp = self.app.post('/models', data={"body.name": "test"})
        assert resp.status_code == 200
        resp = self.app.post(
            '/models',
            data=json.dumps({"name": "test"}),
            content_type="application/json"
        )
        assert resp.status_code == 200

    def test_get_status_sig(self):
        resp = self.app.get('/status_sig')
        assert resp.status_code == 201

    def test_get_status_response(self):
        resp = self.app.get('/status_response')
        assert resp.status_code == 201

    def test_custom_clientside_error(self):
        r = self.app.get(
            '/models/test/secret',
            headers={'Accept': 'application/json'}
        )
        assert r.status_code == 403, r.status_code
        assert json.loads(r.data)['faultstring'] == '403: Forbidden'

        r = self.app.get(
            '/models/test/secret',
            headers={'Accept': 'application/xml'}
        )
        assert r.status_code == 403, r.status_code
        assert r.data == six.b('<error><faultcode>Client</faultcode>'
                               '<faultstring>403: Forbidden</faultstring>'
                               '<debuginfo /></error>')

    def test_custom_non_http_clientside_error(self):
        r = self.app.get(
            '/models/test/custom-error',
            headers={'Accept': 'application/json'}
        )
        assert r.status_code == 412, r.status_code
        assert json.loads(r.data)['faultstring'] == 'FOO!'

        r = self.app.get(
            '/models/test/custom-error',
            headers={'Accept': 'application/xml'}
        )
        assert r.status_code == 412, r.status_code
        assert r.data == six.b('<error><faultcode>Client</faultcode>'
                               '<faultstring>FOO!</faultstring>'
                               '<debuginfo /></error>')

    def test_serversideerror(self):
        r = self.app.get('/divide_by_zero')
        assert r.status_code == 500
        data = json.loads(r.data)
        self.assertEqual(data['debuginfo'], None)
        self.assertEqual(data['faultcode'], 'Server')
        # The faultstring might be one of:
        #  python2: "integer division or modulo by zero
        #  python3: "division by zero"
        self.assert_('division' in data['faultstring'])
        self.assert_('by zero' in data['faultstring'])

if __name__ == '__main__':
    test_app.run()
