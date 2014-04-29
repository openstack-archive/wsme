import unittest
import six

from wsme import types


class TestMultiType(unittest.TestCase):

    def setUp(self):
        self.mt = types.MultiType(types.text, six.integer_types)

    def test_valid_values(self):
        value = self.mt.validate("hello")
        self.assertEqual("hello", value)
        value = self.mt.validate(10)
        self.assertEqual(10, value)

    def test_invalid_values(self):
        self.assertRaises(ValueError, self.mt.validate, 0.10)
        self.assertRaises(ValueError, self.mt.validate, object())

    def test_string_representation(self):
        self.assertEqual(str(self.mt), " | ".join([str(types.text), str(six.integer_types)]))
