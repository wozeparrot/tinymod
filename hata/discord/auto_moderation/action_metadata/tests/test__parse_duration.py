import vampytest

from ..fields import parse_duration


def test__parse_duration():
    """
    Tests whether ``parse_duration`` works as intended.
    """
    for input_data, expected_output in (
        ({}, 0),
        ({'duration_seconds': 1}, 1),
    ):
        output = parse_duration(input_data)
        vampytest.assert_eq(output, expected_output)
