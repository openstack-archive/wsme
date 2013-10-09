import decimal
import datetime
import re
from six.moves import builtins, http_client

try:
    import dateutil.parser
except:
    dateutil = None  # noqa

date_re = r'(?P<year>-?\d{4,})-(?P<month>\d{2})-(?P<day>\d{2})'
time_re = r'(?P<hour>\d{2}):(?P<min>\d{2}):(?P<sec>\d{2})' + \
          r'(\.(?P<sec_frac>\d+))?'
tz_re = r'((?P<tz_sign>[+-])(?P<tz_hour>\d{2}):(?P<tz_min>\d{2}))' + \
        r'|(?P<tz_z>Z)'

datetime_re = re.compile(
    '%sT%s(%s)?' % (date_re, time_re, tz_re))
date_re = re.compile(date_re)
time_re = re.compile(time_re)


if hasattr(builtins, '_'):
    _ = builtins._
else:
    def _(s):
        return s


def parse_isodate(value):
    m = date_re.match(value)
    if m is None:
        raise ValueError("'%s' is not a legal date value" % (value))
    try:
        return datetime.date(
            int(m.group('year')),
            int(m.group('month')),
            int(m.group('day')))
    except ValueError:
        raise ValueError("'%s' is a out-of-range date" % (value))


def parse_isotime(value):
    m = time_re.match(value)
    if m is None:
        raise ValueError("'%s' is not a legal time value" % (value))
    try:
        ms = 0
        if m.group('sec_frac') is not None:
            f = decimal.Decimal('0.' + m.group('sec_frac'))
            f = str(f.quantize(decimal.Decimal('0.000001')))
            ms = int(f[2:])
        return datetime.time(
            int(m.group('hour')),
            int(m.group('min')),
            int(m.group('sec')),
            ms)
    except ValueError:
        raise ValueError("'%s' is a out-of-range time" % (value))


# TODO handle timezone
def parse_isodatetime(value):
    if dateutil:
        return dateutil.parser.parse(value)
    m = datetime_re.match(value)
    if m is None:
        raise ValueError("'%s' is not a legal datetime value" % (value))
    try:
        ms = 0
        if m.group('sec_frac') is not None:
            f = decimal.Decimal('0.' + m.group('sec_frac'))
            f = f.quantize(decimal.Decimal('0.000001'))
            ms = int(str(f)[2:])
        return datetime.datetime(
            int(m.group('year')),
            int(m.group('month')),
            int(m.group('day')),
            int(m.group('hour')),
            int(m.group('min')),
            int(m.group('sec')),
            ms)
    except ValueError:
        raise ValueError("'%s' is a out-of-range datetime" % (value))


def is_valid_code(code_value):
    """
    This function checks if incoming value in http response codes range.
    """
    return code_value in http_client.responses


def is_client_error(code):
    """ Checks client error code (RFC 2616)."""
    return 400 <= code < 500


try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict  # noqa
