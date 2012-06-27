import datetime

from six import u
import six

import xml.etree.ElementTree as et

from simplegeneric import generic

from wsme.protocols.rest import RestProtocol
import wsme.types

import re

time_re = re.compile(r'(?P<h>[0-2][0-9]):(?P<m>[0-5][0-9]):(?P<s>[0-6][0-9])')


def xml_indent(elem, level=0):
    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        for e in elem:
            xml_indent(e, level + 1)
        if not e.tail or not e.tail.strip():
            e.tail = i
    if level and (not elem.tail or not elem.tail.strip()):
        elem.tail = i


@generic
def toxml(datatype, key, value):
    """
    A generic converter from python to xml elements.

    If a non-complex user specific type is to be used in the api,
    a specific toxml should be added::

        from wsme.protocol.restxml import toxml

        myspecialtype = object()

        @toxml.when_object(myspecialtype)
        def myspecialtype_toxml(datatype, key, value):
            el = et.Element(key)
            if value is None:
                el.set('nil', 'true')
            else:
                el.text = str(value)
            return el
    """
    el = et.Element(key)
    if value is None:
        el.set('nil', 'true')
    else:
        if wsme.types.isusertype(datatype):
            return toxml(datatype.basetype,
                            key, datatype.tobasetype(value))
        elif wsme.types.iscomplex(datatype):
            for attrdef in datatype._wsme_attributes:
                attrvalue = getattr(value, attrdef.key)
                if attrvalue is not wsme.types.Unset:
                    el.append(toxml(attrdef.datatype, attrdef.name,
                                    attrvalue))
        else:
            el.text = six.text_type(value)
    return el


@generic
def fromxml(datatype, element):
    """
    A generic converter from xml elements to python datatype.

    If a non-complex user specific type is to be used in the api,
    a specific fromxml should be added::

        from wsme.protocol.restxml import fromxml

        class MySpecialType(object):
            pass

        @fromxml.when_object(MySpecialType)
        def myspecialtype_fromxml(datatype, element):
            if element.get('nil', False):
                return None
            return MySpecialType(element.text)
    """
    if element.get('nil', False):
        return None
    if wsme.types.isusertype(datatype):
        return datatype.frombasetype(
                fromxml(datatype.basetype, element))
    if wsme.types.iscomplex(datatype):
        obj = datatype()
        for attrdef in datatype._wsme_attributes:
            sub = element.find(attrdef.name)
            if sub is not None:
                setattr(obj, attrdef.key, fromxml(attrdef.datatype, sub))
        return obj
    if datatype is wsme.types.bytes:
        return element.text.encode('ascii')
    return datatype(element.text)


@toxml.when_type(wsme.types.ArrayType)
def array_toxml(datatype, key, value):
    el = et.Element(key)
    if value is None:
        el.set('nil', 'true')
    else:
        for item in value:
            el.append(toxml(datatype.item_type, 'item', item))
    return el


@toxml.when_type(wsme.types.DictType)
def dict_toxml(datatype, key, value):
    el = et.Element(key)
    if value is None:
        el.set('nil', 'true')
    else:
        for item in value.items():
            key = toxml(datatype.key_type, 'key', item[0])
            value = toxml(datatype.value_type, 'value', item[1])
            node = et.Element('item')
            node.append(key)
            node.append(value)
            el.append(node)
    return el


@toxml.when_object(wsme.types.bytes)
def bytes_toxml(datatype, key, value):
    el = et.Element(key)
    if value is None:
        el.set('nil', 'true')
    else:
        el.text = value.decode('ascii')
    return el


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


@fromxml.when_type(wsme.types.ArrayType)
def array_fromxml(datatype, element):
    if element.get('nil') == 'true':
        return None
    return [
        fromxml(datatype.item_type, item)
        for item in element.findall('item')
    ]


@fromxml.when_type(wsme.types.DictType)
def dict_fromxml(datatype, element):
    if element.get('nil') == 'true':
        return None
    return dict((
        (fromxml(datatype.key_type, item.find('key')),
            fromxml(datatype.value_type, item.find('value')))
        for item in element.findall('item')))


@fromxml.when_object(datetime.date)
def date_fromxml(datatype, element):
    if element.get('nil') == 'true':
        return None
    return datetime.datetime.strptime(element.text, '%Y-%m-%d').date()


@fromxml.when_object(datetime.time)
def time_fromxml(datatype, element):
    if element.get('nil') == 'true':
        return None
    m = time_re.match(element.text)
    if m:
        return datetime.time(
            int(m.group('h')),
            int(m.group('m')),
            int(m.group('s')))


@fromxml.when_object(datetime.datetime)
def datetime_fromxml(datatype, element):
    if element.get('nil') == 'true':
        return None
    return datetime.datetime.strptime(element.text, '%Y-%m-%dT%H:%M:%S')


class RestXmlProtocol(RestProtocol):
    """
    REST+XML protocol.

    .. autoattribute:: name
    .. autoattribute:: dataformat
    .. autoattribute:: content_types
    """
    name = 'restxml'
    displayname = 'REST+Xml'
    dataformat = 'xml'
    content_types = ['text/xml']

    def decode_arg(self, value, arg):
        return fromxml(arg.datatype, value)

    def parse_arg(self, name, value):
        return et.fromstring(u("<%s>%s</%s>") % (name, value, name))

    def parse_args(self, body):
        return dict((sub.tag, sub) for sub in et.fromstring(body))

    def encode_result(self, context, result):
        return et.tostring(
            toxml(context.funcdef.return_type, 'result', result))

    def encode_error(self, context, errordetail):
        el = et.Element('error')
        et.SubElement(el, 'faultcode').text = errordetail['faultcode']
        et.SubElement(el, 'faultstring').text = errordetail['faultstring']
        if 'debuginfo' in errordetail:
            et.SubElement(el, 'debuginfo').text = errordetail['debuginfo']
        return et.tostring(el)

    def encode_sample_value(self, datatype, value, format=False):
        r = toxml(datatype, 'value', value)
        if format:
            xml_indent(r)
        content = et.tostring(r)
        return ('xml', content)

    def encode_sample_params(self, params, format=False):
        node = et.Element('parameters')
        for name, datatype, value in params:
            node.append(toxml(datatype, name, value))
        if format:
            xml_indent(node)
        content = et.tostring(node)
        return ('xml', content)

    def encode_sample_result(self, datatype, value, format=False):
        r = toxml(datatype, 'result', value)
        if format:
            xml_indent(r)
        content = et.tostring(r)
        return ('xml', content)
