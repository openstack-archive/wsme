import base64
import datetime

try:
    import xml.etree.ElementTree as et
except ImportError:
    import cElementTree as et

from simplegeneric import generic

from wsme.rest import RestProtocol
from wsme.controller import register_protocol
import wsme.types


@generic
def toxml(datatype, key, value):
    el = et.Element(key)
    if value is None:
        el.set('nil', 'true')
    else:
        if wsme.types.isstructured(datatype):
            for key, attrdef in datatype._wsme_attributes:
                el.append(toxml(attrdef.datatype, key, getattr(value, key)))
        else:
            el.text = unicode(value)
    return el


@toxml.when_object(datetime.date)
def date_toxml(datatype, key, value):
    el = et.Element(key)
    if value is None:
        el.set('nil', 'true')
    else:
        el.text = value.isoformat()
    return el


@toxml.when_object(datetime.datetime)
def datetime_toxml(datatype, key, value):
    el = et.Element(key)
    if value is None:
        el.set('nil', 'true')
    else:
        el.text = value.isoformat()
    return el


@toxml.when_object(wsme.types.binary)
def binary_toxml(datatype, key, value):
    el = et.Element(key)
    if value is None:
        el.set('nil', 'true')
    else:
        el.text = base64.encodestring(value)
    return el

        
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
        return et.tostring(toxml(return_type, 'result', result))

    def encode_error(self, errordetail):
        el = et.Element('error')
        et.SubElement(el, 'faultcode').text = errordetail['faultcode']
        et.SubElement(el, 'faultstring').text = errordetail['faultstring']
        if 'debuginfo' in errordetail:
            et.SubElement(el, 'debuginfo').text = errordetail['debuginfo']
        return et.tostring(el)

register_protocol(RestXmlProtocol)
