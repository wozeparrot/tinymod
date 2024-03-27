import vampytest

from ..fields import put_image_small_into


def test__put_image_small_into():
    """
    Tests whether ``put_image_small_into`` is working as intended.
    """
    for input_value, defaults, expected_output in (
        (None, False, {}),
        ('a', False, {'small_image': 'a'}),
    ):
        data = put_image_small_into(input_value, {}, defaults)
        vampytest.assert_eq(data, expected_output)
