import decimal
import datetime
import base64

from six import u
import six

import wsme.tests.protocol
from wsme.utils import parse_isodatetime, parse_isodate, parse_isotime
from wsme.types import isusertype, register_type

from wsme.protocols.restxml import fromxml, toxml

try:
    import xml.etree.ElementTree as et
except:
    import cElementTree as et


def dumpxml(key, obj, datatype=None):
    el = et.Element(key)
    if isinstance(obj, tuple):
        obj, datatype = obj
    if isinstance(datatype, list):
        for item in obj:
            el.append(dumpxml('item', item, datatype[0]))
    elif isinstance(datatype, dict):
        for item in obj.items():
            node = et.SubElement(el, 'item')
            node.append(dumpxml('key', item[0], datatype.keys()[0]))
            node.append(dumpxml('value', item[1], datatype.values()[0]))
    elif datatype == wsme.types.binary:
        el.text = base64.encodestring(obj)
    elif isinstance(obj, six.string_types):
        el.text = obj
    elif type(obj) in (int, float, decimal.Decimal):
        el.text = str(obj)
    elif type(obj) in (datetime.date, datetime.time, datetime.datetime):
        el.text = obj.isoformat()
    elif hasattr(datatype, '_wsme_attributes'):
        for attr in datatype._wsme_attributes:
            name = attr.name
            if name not in obj:
                continue
            o = obj[name]
            el.append(dumpxml(name, o, attr.datatype))
    elif type(obj) == dict:
        for name, value in obj.items():
            el.append(dumpxml(name, value))
    return el


def loadxml(el, datatype):
    print (el, datatype, len(el))
    if el.get('nil') == 'true':
        return None
    if isinstance(datatype, list):
        return [loadxml(item, datatype[0]) for item in el.findall('item')]
    elif isinstance(datatype, dict):
        return dict((
            (loadxml(item.find('key'), datatype.keys()[0]),
                loadxml(item.find('value'), datatype.values()[0]))
            for item in el.findall('item')
        ))
    elif len(el):
        d = {}
        for attr in datatype._wsme_attributes:
            name = attr.name
            child = el.find(name)
            print (name, attr, child)
            if child is not None:
                d[name] = loadxml(child, attr.datatype)
        print (d)
        return d
    else:
        if datatype == wsme.types.binary:
            return base64.decodestring(el.text)
        if isusertype(datatype):
            datatype = datatype.basetype
        if datatype == datetime.date:
            return parse_isodate(el.text)
        if datatype == datetime.time:
            return parse_isotime(el.text)
        if datatype == datetime.datetime:
            return parse_isodatetime(el.text)
        if datatype is None:
            return el.text
        return datatype(el.text)


class TestRestXML(wsme.tests.protocol.ProtocolTestCase):
    protocol = 'restxml'

    def call(self, fpath, _rt=None, _accept=None,
                _no_result_decode=False, **kw):
        el = dumpxml('parameters', kw)
        content = et.tostring(el)
        headers = {
            'Content-Type': 'text/xml',
        }
        if _accept is not None:
            headers['Accept'] = _accept
        res = self.app.post(
            '/' + fpath,
            content,
            headers=headers,
            expect_errors=True)
        print ("Received:", res.body)

        if _no_result_decode:
            return res

        el = et.fromstring(res.body)
        if el.tag == 'error':
            raise wsme.tests.protocol.CallException(
                    el.find('faultcode').text,
                    el.find('faultstring').text,
                    el.find('debuginfo') is not None and
                        el.find('debuginfo').text or None)

        else:
            return loadxml(et.fromstring(res.body), _rt)

    def test_encode_sample_value(self):
        class MyType(object):
            aint = int
            aunicode = unicode

        register_type(MyType)

        value = MyType()
        value.aint = 5
        value.aunicode = u('test')

        language, sample = self.root.protocols[0].encode_sample_value(
            MyType, value, True)
        print (language, sample)

        assert language == 'xml'
        assert sample == """<value>
  <aint>5</aint>
  <aunicode>test</aunicode>
</value>"""

    def test_nil_fromxml(self):
        for dt in (
                str, [int], {int: str}, bool,
                datetime.date, datetime.time, datetime.datetime):
            e = et.Element('value', nil='true')
            assert fromxml(dt, e) is None

    def test_nil_toxml(self):
        for dt in (
                [int], {int: str}, bool,
                datetime.date, datetime.time, datetime.datetime):
            x = et.tostring(toxml(dt, 'value', None))
            assert x == '<value nil="true" />', x

    def test_parse_arg(self):
        e = self.root.protocols[0].parse_arg('value', '5')
        assert e.text == '5'
        assert e.tag == 'value'
