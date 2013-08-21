from six.moves import http_client
from test.tests import FunctionalTest
import json
import pecan

used_status_codes = [400, 401, 404, 500]
http_response_messages = {
    code: '{} {}'.format(code, status)
    for code, status in http_client.responses.iteritems()
    if code in used_status_codes
}


class TestWS(FunctionalTest):

    def test_get_all(self):
        self.app.get('/authors')

    def test_optional_array_param(self):
        r = self.app.get('/authors?q=a&q=b')
        l = json.loads(r.body)
        print l
        assert len(l) == 2
        assert l[0]['firstname'] == 'a'
        assert l[1]['firstname'] == 'b'

    def test_optional_indexed_array_param(self):
        r = self.app.get('/authors?q[0]=a&q[1]=b')
        l = json.loads(r.body)
        print l
        assert len(l) == 2
        assert l[0]['firstname'] == 'a'
        assert l[1]['firstname'] == 'b'

    def test_options_object_array_param(self):
        r = self.app.get('/authors?r.value=a&r.value=b')
        l = json.loads(r.body)
        print l
        assert len(l) == 2
        assert l[0]['firstname'] == 'a'
        assert l[1]['firstname'] == 'b'

    def test_options_indexed_object_array_param(self):
        r = self.app.get('/authors?r[0].value=a&r[1].value=b')
        l = json.loads(r.body)
        print l
        assert len(l) == 2
        assert l[0]['firstname'] == 'a'
        assert l[1]['firstname'] == 'b'

    def test_get_author(self):
        a = self.app.get(
            '/authors/1.json',
        )
        print a
        a = json.loads(a.body)
        print a

        assert a['id'] == 1
        assert a['firstname'] == 'aname'

        a = self.app.get(
            '/authors/1.xml',
        )
        print a
        assert '<id>1</id>' in a.body
        assert '<firstname>aname</firstname>' in a.body

    def test_post_body_parameter(self):
        res = self.app.post(
            '/authors', '{"firstname": "test"}',
            headers={"Content-Type": "application/json"}
        )
        assert res.status_int == 201
        a = json.loads(res.body)
        print a
        assert a['id'] == 10
        assert a['firstname'] == 'test'

    def test_clientsideerror(self):
        expected_status_code = 400
        expected_status = http_response_messages[expected_status_code]
        res = self.app.get(
            '/authors/999.json',
            expect_errors=True
        )
        print res
        self.assertEqual(res.status, expected_status)
        a = json.loads(res.body)
        print a
        assert a['faultcode'] == 'Client'

        res = self.app.get(
            '/authors/999.xml',
            expect_errors=True
        )
        print res
        self.assertEqual(res.status, expected_status)
        assert '<faultcode>Client</faultcode>' in res.body

    def test_custom_clientside_error(self):
        expected_status_code = 404
        expected_status = http_response_messages[expected_status_code]
        res = self.app.get(
            '/authors/998.json',
            expect_errors=True
        )
        print res
        self.assertEqual(res.status, expected_status)
        a = json.loads(res.body)
        print a
        assert a['faultcode'] == 'Server'

        res = self.app.get(
            '/authors/998.xml',
            expect_errors=True
        )
        print res
        self.assertEqual(res.status, expected_status)
        assert '<faultcode>Server</faultcode>' in res.body

    def test_custom_non_http_clientside_error(self):
        expected_status_code = 500
        expected_status = http_response_messages[expected_status_code]
        res = self.app.get(
            '/authors/997.json',
            expect_errors=True
        )
        print res
        self.assertEqual(res.status, expected_status)
        a = json.loads(res.body)
        print a
        assert a['faultcode'] == 'Server'

        res = self.app.get(
            '/authors/997.xml',
            expect_errors=True
        )
        print res
        self.assertEqual(res.status, expected_status)
        assert '<faultcode>Server</faultcode>' in res.body

    def test_non_default_response(self):
        expected_status_code = 401
        expected_status = http_response_messages[expected_status_code]
        res = self.app.get(
            '/authors/911.json',
            expect_errors=True
        )
        self.assertEqual(res.status_int, expected_status_code)
        self.assertEqual(res.status, expected_status)

    def test_serversideerror(self):
        expected_status_code = 500
        expected_status = http_response_messages[expected_status_code]
        res = self.app.get('/divide_by_zero.json', expect_errors=True)
        self.assertEqual(res.status, expected_status)
        a = json.loads(res.body)
        print a
        assert a['faultcode'] == 'Server'
        assert a['debuginfo'] is None

    def test_serversideerror_with_debug(self):
        expected_status_code = 500
        expected_status = http_response_messages[expected_status_code]
        pecan.set_config({'wsme': {'debug': True}})
        res = self.app.get('/divide_by_zero.json', expect_errors=True)
        self.assertEqual(res.status, expected_status)
        a = json.loads(res.body)
        print a
        assert a['faultcode'] == 'Server'
        assert a['debuginfo'].startswith('Traceback (most recent call last):')

    def test_body_parameter(self):
        res = self.app.put(
            '/authors/1/books/2.json',
            '{"name": "Alice au pays des merveilles"}',
            headers={"Content-Type": "application/json"}
        )
        book = json.loads(res.body)
        print book
        assert book['id'] == 2
        assert book['author']['id'] == 1

    def test_no_content_type_if_no_return_type(self):
        res = self.app.delete('/authors/4')
        assert "Content-Type" not in res.headers, res.headers['Content-Type']
