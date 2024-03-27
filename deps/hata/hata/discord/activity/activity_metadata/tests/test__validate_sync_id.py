import vampytest

from ..fields import validate_sync_id


def test__validate_sync_id__0():
    """
    Tests whether `validate_sync_id` works as intended.
    
    Case: passing.
    """
    for input_value, expected_output in (
        (None, None),
        ('', None),
        ('a', 'a'),
    ):
        output = validate_sync_id(input_value)
        vampytest.assert_eq(output, expected_output)


def test__validate_sync_id__1():
    """
    Tests whether `validate_sync_id` works as intended.
    
    Case: `TypeError`.
    """
    for input_value in (
        12.6,
    ):
        with vampytest.assert_raises(TypeError):
            validate_sync_id(input_value)
