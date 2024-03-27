import vampytest

from ..fields import put_open_into


def test__put_open_into():
    """
    Tests whether ``put_open_into`` is working as intended.
    """
    for input_value, defaults, expected_output in (
        (True, False, {}),
        (True, True, {'thread_metadata': {'locked': False}}),
        (False, False, {'thread_metadata': {'locked': True}}),
    ):
        data = put_open_into(input_value, {}, defaults)
        vampytest.assert_eq(data, expected_output)
