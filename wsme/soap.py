"""
A SOAP implementation for wsme.
Parts of the code were taken from the tgwebservices soap implmentation.
"""

import pkg_resources
import datetime
import decimal
import base64

from simplegeneric import generic

try:
    from xml.etree import cElementTree as et
except ImportError:
    import cElementTree as et

from genshi.builder import tag, Element, Namespace
from genshi.template import MarkupTemplate
from wsme.controller import register_protocol, pexpose
import wsme.types

type_registry = {
    basestring: 'xsd:string',
    str: 'xsd:string',
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
    response output"""
    return make_soap_element(datatype, tag, value)

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

class SoapProtocol(object):
    name = 'SOAP'
    content_types = ['application/soap+xml']

    ns = {
        "soap": "http://www.w3.org/2001/12/soap-envelope",
        "soapenv": "http://schemas.xmlsoap.org/soap/envelope/",
        "soapenc": "http://schemas.xmlsoap.org/soap/encoding/",
    }

    def __init__(self, tns=None,
            typenamespace=None,
            baseURL=None
            ):
        self.tns = tns
        self.typenamespace = typenamespace
        self.servicename = 'MyApp'
        self._name_mapping = {}

    def get_name_mapping(self, service=None):
        if service not in self._name_mapping:
            self._name_mapping[service] = dict(
                (self.soap_fname(f), f.path + [f.name])
                for f in self.root.getapi() if service is None or (f.path and f.path[0] == service)
            )
            print self._name_mapping
        return self._name_mapping[service]


    def accept(self, req):
        if req.path.endswith('.wsdl'):
            return True
        for ct in self.content_types:
            if req.headers['Content-Type'].startswith(ct):
                return True
        return False

    def extract_path(self, request):
        if request.path.endswith('.wsdl'):
            return ['_protocol', self.name, 'api_wsdl']
        el = et.fromstring(request.body)
        body = el.find('{%(soapenv)s}Body' % self.ns)
        # Extract the service name from the tns
        fname = list(body)[0].tag
        if fname.startswith('{%s}' % self.typenamespace):
            fname = fname[len(self.typenamespace)+2:]
            print fname
            return self.get_name_mapping()[fname]
        return None

    def read_arguments(self, funcdef, request):
        return {}

    def soap_response(self, funcdef, result):
        r = Element(self.soap_fname(funcdef) + 'Response')
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
            tns = self.tns,
            typenamespace = self.typenamespace,
            soapenc = self.ns['soapenc'],
            service_name = servicename,
            complex_types = (t() for t in wsme.types.complex_types),
            funclist = self.root.getapi(),
            arrays = [],
            list_attributes = wsme.types.list_attributes,
            baseURL = service,
            soap_type = self.soap_type,
            soap_fname = self.soap_fname,
        )

    def soap_type(self, datatype):
        if datatype in type_registry:
            return type_registry[datatype]
        if wsme.types.iscomplex(datatype):
            return "types:%s" % datatype.__name__

    def soap_fname(self, funcdef):
        return "%s%s" % (
            "".join((i.capitalize() for i in funcdef.path)),
            funcdef.name.capitalize())

register_protocol(SoapProtocol)
