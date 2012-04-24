import datetime
import unittest

from wsme.utils import parse_isodate, parse_isotime, parse_isodatetime


class TestUtils(unittest.TestCase):
    def test_parse_isodate(self):
        good_dates = [
            ('2008-02-01', datetime.date(2008, 2, 1)),
            ('2009-01-04', datetime.date(2009, 1, 4)),
        ]
        ill_formatted_dates = [
            '24-12-2004'
        ]
        out_of_range_dates = [
            '0000-00-00',
            '2012-02-30',
        ]
        for s, d in good_dates:
            assert parse_isodate(s) == d
        for s in ill_formatted_dates + out_of_range_dates:
            self.assertRaises(ValueError, parse_isodate, s)

    def test_parse_isotime(self):
        good_times = [
            ('12:03:54', datetime.time(12, 3, 54)),
            ('23:59:59.000004', datetime.time(23, 59, 59, 4)),
        ]
        ill_formatted_times = [
            '24-12-2004'
        ]
        out_of_range_times = [
            '32:12:00',
            '00:54:60',
        ]
        for s, t in good_times:
            assert parse_isotime(s) == t
        for s in ill_formatted_times + out_of_range_times:
            self.assertRaises(ValueError, parse_isotime, s)

    def test_parse_isodatetime(self):
        good_datetimes = [
            ('2008-02-12T12:03:54',
                datetime.datetime(2008, 2, 12, 12, 3, 54)),
            ('2012-05-14T23:59:59.000004',
                datetime.datetime(2012, 5, 14, 23, 59, 59, 4)),
        ]
        ill_formatted_datetimes = [
            '24-12-2004'
        ]
        out_of_range_datetimes = [
            '2008-02-12T32:12:00',
            '2012-13-12T00:54:60',
        ]
        for s, t in good_datetimes:
            assert parse_isodatetime(s) == t
        for s in ill_formatted_datetimes + out_of_range_datetimes:
            self.assertRaises(ValueError, parse_isodatetime, s)
