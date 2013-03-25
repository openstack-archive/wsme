import unittest
from flask import Flask
from wsmeext.flask import signature

test_app = Flask(__name__)


@test_app.route('/multiply')
@signature(int, int, int)
def multiply(a, b):
    return a * b


@test_app.route('/divide_by_zero')
@signature(None)
def divide_by_zero():
    return 1 / 0


class FlaskrTestCase(unittest.TestCase):

    def setUp(self):
        test_app.config['TESTING'] = True
        self.app = test_app.test_client()

    def tearDown(self):
        pass

    def test_multiply(self):
        r = self.app.get('/multiply?a=2&b=5')
        assert r.data == '10'

    def test_serversideerror(self):
        r = self.app.get('/divide_by_zero')
        assert r.status_code == 500
        self.assertEquals(
            r.data,
            '{"debuginfo": null, "faultcode": "Server", "faultstring": "integer division or modulo by zero"}'
        )

if __name__ == '__main__':
    test_app.run()
