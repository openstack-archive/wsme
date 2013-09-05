from wsmeext.utils import is_valid_code


class TestUtils():

    def test_validator_with_valid_code(self):
        valid_code = 404
        assert is_valid_code(valid_code), "Valid status code not detected"

    def test_validator_with_invalid_int_code(self):
        invalid_int_code = 648
        assert (
            not is_valid_code(invalid_int_code),
            "Invalid status code not detected"
        )

    def test_validator_with_invalid_str_code(self):
        invalid_str_code = '404'
        assert (
            not is_valid_code(invalid_str_code),
            "Invalid status code not detected"
        )
