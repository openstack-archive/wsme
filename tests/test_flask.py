import unittest
from flask import Flask
from wsmeext.flask import signature

test_app = Flask(__name__)


@test_app.route('/multiply')
@signature(int, int, int)
def multiply(a, b):
    return a * b


class FlaskrTestCase(unittest.TestCase):

    def setUp(self):
        test_app.config['TESTING'] = True
        self.app = test_app.test_client()

    def tearDown(self):
        pass

    def test_multiply(self):
        r = self.app.get('/multiply?a=2&b=5')
        assert r.data == '10'

if __name__ == '__main__':
    test_app.run()
