"""
A SOAP implementation for wsme.
Parts of the code were taken from the tgwebservices soap implmentation.
"""

import pkg_resources
import datetime
import decimal
import base64
import logging

from simplegeneric import generic

try:
    from xml.etree import cElementTree as et
except ImportError:
    import cElementTree as et

from genshi.builder import tag, Element, Namespace
from genshi.template import MarkupTemplate
from wsme.controller import register_protocol, pexpose
import wsme.types
from wsme import exc
from wsme.utils import *

log = logging.getLogger(__name__)

xsi_ns = 'http://www.w3.org/2001/XMLSchema-instance'
type_qn = '{%s}type' % xsi_ns
nil_qn = '{%s}nil' % xsi_ns


type_registry = {
    basestring: 'xsd:string',
    str: 'xsd:string',
    unicode: 'xsd:string',
    int: 'xsd:int',
    long: "xsd:long",
    float: "xsd:float",
    bool: "xsd:boolean",
    #unsigned: "xsd:unsignedInt",
    datetime.datetime: "xsd:dateTime",
    datetime.date: "xsd:date",
    datetime.time: "xsd:time",
    decimal.Decimal: "xsd:decimal",
    wsme.types.binary: "xsd:base64Binary",
}

array_registry = {
    basestring: "String_Array",
    str: "String_Array",
    unicode: "String_Array",
    int: "Int_Array",
    long: "Long_Array",
    float: "Float_Array",
    bool: "Boolean_Array",
}


def soap_array(datatype):
    if datatype in array_registry:
        return array_registry[datatype]
    return 'types:' + datatype.__name__ + '_Array'


def soap_type(datatype):
    if type(datatype) == list:
        return soap_array(datatype[0])
    if datatype in type_registry:
        return type_registry[datatype]
    if wsme.types.iscomplex(datatype):
        return "types:%s" % datatype.__name__


def soap_fname(funcdef):
    return "%s%s" % (
        "".join((i.capitalize() for i in funcdef.path)),
        funcdef.name.capitalize())


def make_soap_element(datatype, tag, value):
    el = Element(tag)
    if value is None:
        el(**{'xsi:nil': 'true'})
    elif wsme.types.iscomplex(datatype):
        el(**{'xsi:type': datatype.__name__})
        for name, attrdef in wsme.types.list_attributes(datatype):
            el.append(
                tosoap(attrdef.datatype, name, getattr(value, name)))
    else:
        el(value, **{'xsi:type': type_registry.get(datatype)})
    return el


@generic
def tosoap(datatype, tag, value):
    """Converts a value into xml Element objects for inclusion in the SOAP
    response output (after adding the type to the type_registry).
    
    If a non-complex user specific type is to be used in the api,
    a specific toxml should be added::

        from wsme.protocol.soap import tosoap, make_soap_element, type_registry

        class MySpecialType(object):
            pass

        type_registry[MySpecialType] = 'xsd:MySpecialType'

        @tosoap.when_object(MySpecialType)
        def myspecialtype_tosoap(datatype, tag, value):
            return make_soap_element(datatype, tag, str(value))
    """
    return make_soap_element(datatype, tag, value)


@tosoap.when_type(list)
def array_tosoap(datatype, tag, value):
    el = Element(tag)
    el(**{'xsi:type': soap_array(datatype[0])})
    if value is None:
        el(**{'xsi:nil': 'true'})
    for item in value:
        el.append(tosoap(datatype[0], 'item', item))
    return el


@tosoap.when_object(datetime.datetime)
def datetime_tosoap(datatype, tag, value):
    return make_soap_element(datatype, tag,
        value is not None and value.isoformat() or None)


@tosoap.when_object(wsme.types.binary)
def binary_tosoap(datatype, tag, value):
    return make_soap_element(datatype, tag,
        value is not None and base64.encodestring(value)
        or None)


@tosoap.when_object(None)
def None_tosoap(datatype, tag, value):
    return make_soap_element(datatype, tag, None)


@generic
def fromsoap(datatype, el, ns):
    """
    A generic converter from soap elements to python datatype.

    If a non-complex user specific type is to be used in the api,
    a specific fromsoap should be added.
    """
    if el.get(nil_qn) == 'true':
        return None
    soaptype = el.get(type_qn)
    if datatype in type_registry:
        if soaptype != type_registry[datatype]:
            raise exc.InvalidInput(el.tag, et.tostring(el))
        value = datatype(el.text)
    else:
        if soaptype != datatype.__name__:
            raise exc.InvalidInput(el.tag, et.tostring(el))
        value = datatype()
        for name, attr in wsme.types.list_attributes(datatype):
            child = el.find('{%s}%s' % (ns['type'], name))
            setattr(value, name, fromsoap(attr.datatype, child, ns))
    return value


@fromsoap.when_type(list)
def array_fromsoap(datatype, el, ns):
    return [fromsoap(datatype[0], child, ns) for child in el]

@fromsoap.when_object(datetime.date)
def date_fromsoap(datatype, el, ns):
    if el.get(nil_qn) == 'true':
        return None
    if el.get(type_qn) != 'xsd:date':
        raise exc.InvalidInput(el.tag, et.tostring(el))
    return parse_isodate(el.text)


@fromsoap.when_object(datetime.time)
def time_fromsoap(datatype, el, ns):
    if el.get(nil_qn) == 'true':
        return None
    if el.get(type_qn) != 'xsd:time':
        raise exc.InvalidInput(el.tag, et.tostring(el))
    return parse_isotime(el.text)


@fromsoap.when_object(datetime.datetime)
def datetime_fromsoap(datatype, el, ns):
    if el.get(nil_qn) == 'true':
        return None
    if el.get(type_qn) != 'xsd:dateTime':
        raise exc.InvalidInput(el.tag, et.tostring(el))
    return parse_isodatetime(el.text)


@fromsoap.when_object(wsme.types.binary)
def binary_fromsoap(datatype, el, ns):
    if el.get(nil_qn) == 'true':
        return None
    if el.get(type_qn) != 'xsd:base64Binary':
        raise exc.InvalidInput(el.tag, et.tostring(el))
    return base64.decodestring(el.text)


class SoapProtocol(object):
    """
    REST+XML protocol.

    .. autoattribute:: name
    .. autoattribute:: dataformat
    .. autoattribute:: content_types
    """
    name = 'SOAP'
    content_types = ['application/soap+xml']

    ns = {
        "soap": "http://www.w3.org/2001/12/soap-envelope",
        "soapenv": "http://schemas.xmlsoap.org/soap/envelope/",
        "soapenc": "http://schemas.xmlsoap.org/soap/encoding/",
    }

    def __init__(self, tns=None,
            typenamespace=None,
            baseURL=None):
        self.tns = tns
        self.typenamespace = typenamespace
        self.servicename = 'MyApp'
        self.baseURL = baseURL
        self._name_mapping = {}

    def get_name_mapping(self, service=None):
        if service not in self._name_mapping:
            self._name_mapping[service] = dict(
                (soap_fname(f), f.path + [f.name])
                for f in self.root.getapi()
                    if service is None or (f.path and f.path[0] == service))
        return self._name_mapping[service]

    def accept(self, req):
        if req.path.endswith('.wsdl'):
            return True
        for ct in self.content_types:
            if req.headers['Content-Type'].startswith(ct):
                return True
        if req.headers.get("Soapaction"):
            return True
        return False

    def extract_path(self, request):
        if request.path.endswith('.wsdl'):
            return ['_protocol', self.name, 'api_wsdl']
        el = et.fromstring(request.body)
        body = el.find('{%(soapenv)s}Body' % self.ns)
        # Extract the service name from the tns
        message = list(body)[0]
        fname = message.tag
        if fname.startswith('{%s}' % self.typenamespace):
            fname = fname[len(self.typenamespace) + 2:]
            mapping = self.get_name_mapping()
            if fname not in mapping:
                raise exc.UnknownFunction(fname)
            path = mapping[fname]
            request._wsme_soap_message = message
            return path
        return None

    def read_arguments(self, funcdef, request):
        kw = {}
        if not hasattr(request, '_wsme_soap_message'):
            return kw
        msg = request._wsme_soap_message
        parameters = msg.find('{%s}parameters' % self.typenamespace)
        if parameters:
            for param in parameters:
                name = param.tag[len(self.typenamespace) + 2:]
                arg = funcdef.get_arg(name)
                value = fromsoap(arg.datatype, param, {
                    'type': self.typenamespace,
                })
                kw[name] = value

        return kw

    def soap_response(self, funcdef, result):
        r = Element(soap_fname(funcdef) + 'Response')
        r.append(tosoap(funcdef.return_type, 'result', result))
        return r

    def encode_result(self, funcdef, result):
        envelope = self.render_template('soap',
                typenamespace=self.typenamespace,
                result=result,
                funcdef=funcdef,
                soap_response=self.soap_response)
        return envelope

    def get_template(self, name):
        return pkg_resources.resource_string(
            __name__, 'templates/%s.html' % name)

    def render_template(self, name, **kw):
        tmpl = MarkupTemplate(self.get_template(name))
        stream = tmpl.generate(**kw)
        return stream.render('xml')

    def encode_error(self, infos):
        return self.render_template('fault',
            typenamespace=self.typenamespace,
            **infos)

    @pexpose(contenttype="text/xml")
    def api_wsdl(self, service=None):
        if service is None:
            servicename = self.servicename
        else:
            servicename = self.servicename + service.capitalize()
        return self.render_template('wsdl',
            tns=self.tns,
            typenamespace=self.typenamespace,
            soapenc=self.ns['soapenc'],
            service_name=servicename,
            complex_types=(t() for t in wsme.types.complex_types),
            funclist=self.root.getapi(),
            arrays=wsme.types.array_types,
            list_attributes=wsme.types.list_attributes,
            baseURL=self.baseURL,
            soap_array=soap_array,
            soap_type=soap_type,
            soap_fname=soap_fname,
        )

register_protocol(SoapProtocol)
