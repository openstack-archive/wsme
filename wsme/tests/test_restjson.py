from wsme.tests.protocol import TestProtocol
import json

class TestRestJson(TestProtocol):
    protocol = 'REST+Json'
    def call(self, fpath, **kw):
        content = json.dumps(kw)
        res = self.app.post(
            '/' + fpath,
            content,
            headers={
                'Content-Type': 'application/json'
            })
        return json.loads(res.body)
