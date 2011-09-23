import base64
import datetime

try:
    import xml.etree.ElementTree as et
except ImportError:
    import cElementTree as et

from simplegeneric import generic

from wsme.rest import RestProtocol
from wsme.controller import register_protocol
from wsme.exc import *
import wsme.types

import re

time_re = re.compile(r'(?P<h>[0-2][0-9]):(?P<m>[0-5][0-9]):(?P<s>[0-6][0-9])')


@generic
def toxml(datatype, key, value):
    el = et.Element(key)
    if value is None:
        el.set('nil', 'true')
    else:
        if wsme.types.iscomplex(datatype):
            for key, attrdef in datatype._wsme_attributes:
                el.append(toxml(attrdef.datatype, key, getattr(value, key)))
        else:
            el.text = unicode(value)
    return el


@generic
def fromxml(datatype, element):
    if element.get('nil', False):
        return None
    if wsme.types.iscomplex(datatype):
        obj = datatype()
        for key, attrdef in datatype._wsme_attributes:
            sub = element.find(key)
            if sub is not None:
                setattr(obj, key, fromxml(attrdef.datatype, sub))
        return obj
    return datatype(element.text)


@toxml.when_object(bool)
def bool_toxml(datatype, key, value):
    el = et.Element(key)
    if value is None:
        el.set('nil', 'true')
    else:
        el.text = value and 'true' or 'false'
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


@fromxml.when_object(datetime.date)
def date_fromxml(datatype, element):
    return datetime.datetime.strptime(element.text, '%Y-%m-%d').date()


@fromxml.when_object(datetime.time)
def time_fromxml(datatype, element):
    m = time_re.match(element.text)
    if m:
        return datetime.time(
            int(m.group('h')),
            int(m.group('m')),
            int(m.group('s')))


@fromxml.when_object(datetime.datetime)
def datetime_fromxml(datatype, element):
    return datetime.datetime.strptime(element.text, '%Y-%m-%dT%H:%M:%S')


@fromxml.when_object(wsme.types.binary)
def binary_fromxml(datatype, element):
    return base64.decodestring(element.text)


class RestXmlProtocol(RestProtocol):
    name = 'REST+XML'
    dataformat = 'xml'
    content_types = ['text/xml']

    def decode_arg(self, value, arg):
        return fromxml(arg.datatype, value)

    def parse_arg(self, name, value):
        return et.fromstring(u"<%s>%s</%s>" % (name, value, name))

    def parse_args(self, body):
        return dict((sub.tag, sub) for sub in et.fromstring(body))

    def encode_result(self, funcdef, result):
        return et.tostring(toxml(funcdef.return_type, 'result', result))

    def encode_error(self, errordetail):
        el = et.Element('error')
        et.SubElement(el, 'faultcode').text = errordetail['faultcode']
        et.SubElement(el, 'faultstring').text = errordetail['faultstring']
        if 'debuginfo' in errordetail:
            et.SubElement(el, 'debuginfo').text = errordetail['debuginfo']
        return et.tostring(el)

register_protocol(RestXmlProtocol)
