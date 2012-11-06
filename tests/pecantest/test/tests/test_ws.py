from test.tests import FunctionalTest
import json


class TestWS(FunctionalTest):

    def test_get_author(self):
        a = self.app.get(
            '/authors/1.json',
        )
        print a
        a = json.loads(a.body)
        print a

        assert a['id'] == 1

        a = self.app.get(
            '/authors/1.xml',
        )
        print a
        assert '<id>1</id>' in a.body
