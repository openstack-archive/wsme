import unittest
import json

import webtest

from cornice import Service
from pyramid.config import Configurator

from wsme.types import text, Base
from wsmeext.cornice import signature


class User(Base):
    id = int
    name = text

users = Service(name='users', path='/users')


@users.get()
@signature([User])
def users_get():
    return [User(id=1, name='first')]


@users.post()
@signature(User, body=User)
def users_create(data):
    data.id = 2
    return data


def make_app():
    config = Configurator()
    config.include("cornice")
    config.include("wsmeext.cornice")
    config.scan("test_cornice")
    return config.make_wsgi_app()


class WSMECorniceTestCase(unittest.TestCase):
    def setUp(self):
        self.app = webtest.TestApp(make_app())

    def test_get_json_list(self):
        resp = self.app.get('/users')
        self.assertEquals(
            resp.body,
            '[{"id": 1, "name": "first"}]'
        )

    def test_get_xml_list(self):
        resp = self.app.get('/users', headers={"Accept": "text/xml"})
        self.assertEquals(
            resp.body,
            '<result><item><id>1</id><name>first</name></item></result>'
        )

    def test_post_json_data(self):
        data = json.dumps({"name": "new"})
        resp = self.app.post(
            '/users', data,
            headers={"Content-Type": "application/json"}
        )
        self.assertEquals(
            resp.body,
            '{"id": 2, "name": "new"}'
        )

    def test_post_xml_data(self):
        data = '<data><name>new</name></data>'
        resp = self.app.post(
            '/users', data,
            headers={"Content-Type": "text/xml"}
        )
        self.assertEquals(
            resp.body,
            '<result><id>2</id><name>new</name></result>'
        )
