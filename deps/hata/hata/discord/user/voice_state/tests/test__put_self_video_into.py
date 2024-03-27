import vampytest

from ..fields import put_self_video_into


def test__put_self_video_into():
    """
    Tests whether ``put_self_video_into`` works as intended.
    """
    for input_value, defaults, expected_output in (
        (False, False, {'self_video': False}),
        (False, True, {'self_video': False}),
        (True, False, {'self_video': True}),
    ):
        data = put_self_video_into(input_value, {}, defaults)
        vampytest.assert_eq(data, expected_output)
