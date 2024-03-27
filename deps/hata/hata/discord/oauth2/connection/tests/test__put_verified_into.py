import vampytest

from ..fields import put_verified_into


def test__put_verified_into():
    """
    Tests whether ``put_verified_into`` is working as intended.
    """
    for input_value, defaults, expected_output in (
        (False, False, {}),
        (False, True, {'verified': False}),
        (True, False, {'verified': True}),
    ):
        data = put_verified_into(input_value, {}, defaults)
        vampytest.assert_eq(data, expected_output)
