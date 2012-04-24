# encoding=utf8

from wsme.exc import *
from six import u


def test_clientside_error():
    e = ClientSideError("Test")

    assert e.faultstring == "Test"


def test_invalidinput():
    e = InvalidInput('field', 'badvalue', "error message")

    assert e.faultstring == \
        u("Invalid input for field/attribute field. Value: 'badvalue'. " \
        "error message"), e.faultstring


def test_missingargument():
    e = MissingArgument('argname', "error message")

    assert e.faultstring == \
        u('Missing argument: "argname": error message'), e.faultstring


def test_unknownargument():
    e = UnknownArgument('argname', "error message")

    assert e.faultstring == \
        u('Unknown argument: "argname": error message'), e.faultstring
