import cgi
import datetime
import re

from simplegeneric import generic

from wsme.types import iscomplex, list_attributes, Unset
from wsme.types import UserType, ArrayType, DictType, File
from wsme.utils import parse_isodate, parse_isotime, parse_isodatetime


ARRAY_MAX_SIZE = 1000


@generic
def from_param(datatype, value):
    return datatype(value) if value else None


@from_param.when_object(datetime.date)
def date_from_param(datatype, value):
    return parse_isodate(value) if value else None


@from_param.when_object(datetime.time)
def time_from_param(datatype, value):
    return parse_isotime(value) if value else None


@from_param.when_object(datetime.datetime)
def datetime_from_param(datatype, value):
    return parse_isodatetime(value) if value else None


@from_param.when_object(File)
def filetype_from_param(datatype, value):
    if isinstance(value, cgi.FieldStorage):
        return File(fieldstorage=value)
    return File(content=value)


@from_param.when_type(UserType)
def usertype_from_param(datatype, value):
    return datatype.frombasetype(
        from_param(datatype.basetype, value))


@generic
def from_params(datatype, params, path, hit_paths):
    if iscomplex(datatype) and datatype is not File:
        objfound = False
        for key in params:
            if key.startswith(path + '.'):
                objfound = True
                break
        if objfound:
            r = datatype()
            for attrdef in list_attributes(datatype):
                value = from_params(attrdef.datatype,
                        params, '%s.%s' % (path, attrdef.key), hit_paths)
                if value is not Unset:
                    setattr(r, attrdef.key, value)
            return r
    else:
        if path in params:
            hit_paths.add(path)
            return from_param(datatype, params[path])
    return Unset


@from_params.when_type(ArrayType)
def array_from_params(datatype, params, path, hit_paths):
    if path in params:
        return [
            from_param(datatype.item_type, value)
            for value in params.getall(path)]
    else:
        indexes = set()
        r = re.compile('^%s\[(?P<index>\d+)\]' % re.escape(path))

        for p in params.keys():
            m = r.match(p)
            if m:
                indexes.add(int(m.group('index')))

        if not indexes:
            return Unset

        indexes = list(indexes)
        indexes.sort()

        return [from_params(datatype.item_type, params,
                            '%s[%s]' % (path, index), hit_paths)
                for index in indexes]


@from_params.when_type(DictType)
def dict_from_params(datatype, params, path, hit_paths):

    keys = set()
    r = re.compile('^%s\[(?P<key>[a-zA-Z0-9_\.]+)\]' % re.escape(path))

    for p in params.keys():
        m = r.match(p)
        if m:
            keys.add(from_param(datatype.key_type, m.group('key')))

    if not keys:
        return Unset

    return dict((
        (key, from_params(datatype.value_type,
                          params, '%s[%s]' % (path, key), hit_paths))
        for key in keys))
