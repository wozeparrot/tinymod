import vampytest

from ..fields import put_image_large_into


def test__put_image_large_into():
    """
    Tests whether ``put_image_large_into`` is working as intended.
    """
    for input_value, defaults, expected_output in (
        (None, False, {}),
        ('a', False, {'large_image': 'a'}),
    ):
        data = put_image_large_into(input_value, {}, defaults)
        vampytest.assert_eq(data, expected_output)
