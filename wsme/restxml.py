import base64

try:
    import xml.etree.ElementTree as et
except ImportError:
    import cElementTree as et

from wsme.rest import RestProtocol
from wsme.controller import register_protocol
import wsme.types


class RestXmlProtocol(RestProtocol):
    name = 'REST+XML'
    dataformat = 'xml'
    content_types = ['text/xml']

    def decode_args(self, req, arguments):
        el = et.fromstring(req.body)
        assert el.tag == 'parameters'
        kw = {}
        return kw

    def encode_result(self, result, return_type):
        return '<result/>'
        return json.dumps({'result': prepare_encode(result, return_type)})

    def encode_error(self, errordetail):
        el = et.Element('error')
        et.SubElement(el, 'faultcode').text = errordetail['faultcode']
        et.SubElement(el, 'faultstring').text = errordetail['faultstring']
        if 'debuginfo' in errordetail:
            et.SubElement(el, 'debuginfo').text = errordetail['debuginfo']
        return et.tostring(el)

register_protocol(RestXmlProtocol)


