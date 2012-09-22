import unittest

try:
    import simplejson as json
except ImportError:
    import json

from wsme.tests.protocol import WSTestRoot
import wsme.spore


class TestSpore(unittest.TestCase):
    def test_spore(self):
        spore = wsme.spore.getdesc(WSTestRoot())

        print spore

        spore = json.loads(spore)

        assert len(spore['methods']) == 36, len(spore['methods'])

        m = spore['methods']['argtypes_setbytesarray']
        assert m['path'] == '/argtypes/setbytesarray'
        assert m['optional_params'] == ['value']
        assert m['method'] == 'POST'

        m = spore['methods']['argtypes_setdecimal']
        assert m['path'] == '/argtypes/setdecimal'
        assert m['required_params'] == ['value']
        assert m['method'] == 'GET'
