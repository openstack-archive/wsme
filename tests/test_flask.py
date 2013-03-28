import unittest
from flask import Flask, json
from wsmeext.flask import signature
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


@test_app.route('/models', methods=['POST'])
@signature(Model, body=Model)
def post_model(body):
    return Model(name=body.name)


class FlaskrTestCase(unittest.TestCase):

    def setUp(self):
        test_app.config['TESTING'] = True
        self.app = test_app.test_client()

    def tearDown(self):
        pass

    def test_multiply(self):
        r = self.app.get('/multiply?a=2&b=5')
        assert r.data == '10'

    def test_get_model(self):
        resp = self.app.get('/models/test')
        assert resp.status_code == 200

    def test_list_models(self):
        resp = self.app.get('/models')
        assert resp.status_code == 200

    def test_array_parameter(self):
        resp = self.app.get('/models?q.op=%3D&q.attr=name&q.value=second')
        assert resp.status_code == 200
        print resp.data
        self.assertEquals(
            resp.data, '[{"name": "second"}]'
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

    def test_serversideerror(self):
        r = self.app.get('/divide_by_zero')
        assert r.status_code == 500
        self.assertEquals(
            r.data,
            '{"debuginfo": null, "faultcode": "Server", "faultstring": '
            '"integer division or modulo by zero"}'
        )

if __name__ == '__main__':
    test_app.run()
