"""
This File consists of utils functions used in wsmeext module.
"""
from six.moves import http_client


def is_valid_code(code_value):
    """
    This function checks if incoming value in http response codes range.
    """
    return code_value in http_client.responses
