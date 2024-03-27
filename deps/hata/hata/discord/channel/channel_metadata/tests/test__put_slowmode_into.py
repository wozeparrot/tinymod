import vampytest

from ..fields import put_slowmode_into


def test__put_slowmode_into():
    """
    Tests whether ``put_slowmode_into`` is working as intended.
    """
    for input_value, defaults, expected_output in (
        (0, False, {}),
        (0, True, {'rate_limit_per_user': None}),
        (1, False, {'rate_limit_per_user': 1}),
    ):
        data = put_slowmode_into(input_value, {}, defaults)
        vampytest.assert_eq(data, expected_output)
