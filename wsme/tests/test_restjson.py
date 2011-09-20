import wsme.tests.protocol
try:
    import simplejson as json
except:
    import json

import wsme.restjson

class TestRestJson(wsme.tests.protocol.ProtocolTestCase):
    protocol = 'REST+Json'

    def call(self, fpath, **kw):
        content = json.dumps(kw)
        res = self.app.post(
            '/' + fpath,
            content,
            headers={
                'Content-Type': 'application/json',
            },
            expect_errors=True)
        print "Received:", res.body
        r = json.loads(res.body)
        if 'result' in r:
            return r['result']
        else:
            raise wsme.tests.protocol.CallException(
                    r['faultcode'],
                    r['faultstring'],
                    r.get('debuginfo'))

        return json.loads(res.body)
