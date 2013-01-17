from test.tests import FunctionalTest
import json


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

    def test_clientsideerror(self):
        res = self.app.get(
            '/authors/999.json',
            expect_errors=True
        )
        print res
        self.assertEqual(res.status, '400 Bad Request')
        a = json.loads(res.body)
        print a
        assert a['faultcode'] == 'Client'

        res = self.app.get(
            '/authors/999.xml',
            expect_errors=True
        )
        print res
        self.assertEqual(res.status, '400 Bad Request')
        assert '<faultcode>Client</faultcode>' in res.body

    def test_serversideerror(self):
        res = self.app.get('/divide_by_zero.json', expect_errors=True)
        self.assertEqual(res.status, '500 Internal Server Error')
        a = json.loads(res.body)
        print a
        assert a['faultcode'] == 'Server'
