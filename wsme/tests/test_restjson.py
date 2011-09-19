import wsme.tests.protocol
try:
    import simplejson as json
except:
    import json


class TestRestJson(wsme.tests.protocol.ProtocolTestCase):
    protocol = 'REST+Json'

    def call(self, fpath, **kw):
        content = json.dumps(kw)
        res = self.app.post(
            '/' + fpath,
            content,
            headers={
                'Content-Type': 'application/json',
            })
        return json.loads(res.body)

