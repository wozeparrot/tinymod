import vampytest

from ..fields import put_value_into


def test__put_value_into():
    """
    Tests whether ``put_value_into`` works as intended.
    """
    value = 1
    
    for input_value, defaults, expected_output in (
        (value, False, {'id': value}),
    ):
        data = put_value_into(input_value, {}, defaults)
        vampytest.assert_eq(data, expected_output)
