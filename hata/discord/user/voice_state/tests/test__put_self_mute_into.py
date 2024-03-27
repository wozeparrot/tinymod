import vampytest

from ..fields import put_self_mute_into


def test__put_self_mute_into():
    """
    Tests whether ``put_self_mute_into`` works as intended.
    """
    for input_value, defaults, expected_output in (
        (False, False, {'self_mute': False}),
        (False, True, {'self_mute': False}),
        (True, False, {'self_mute': True}),
    ):
        data = put_self_mute_into(input_value, {}, defaults)
        vampytest.assert_eq(data, expected_output)
