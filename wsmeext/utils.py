"""
This File consists of utils functions used in wsmeext module.
"""
try:
    from httplib import responses
except ImportError:
    from http.client import responses


def is_valid_code(code_value):
    """
    This function checks if incoming value in http response codes range.
    """
    return code_value in responses
