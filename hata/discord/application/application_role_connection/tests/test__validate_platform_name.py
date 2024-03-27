import vampytest

from ..constants import PLATFORM_NAME_LENGTH_MAX
from ..fields import validate_platform_name


def test__validate_platform_name__0():
    """
    Tests whether `validate_platform_name` works as intended.
    
    Case: passing.
    """
    for input_value, expected_output in (
        (None, None),
        ('', None),
        ('a', 'a'),
    ):
        output = validate_platform_name(input_value)
        vampytest.assert_eq(output, expected_output)


def test__validate_platform_name__1():
    """
    Tests whether `validate_platform_name` works as intended.
    
    Case: `TypeError`.
    """
    for input_value in (
        12.6,
    ):
        with vampytest.assert_raises(TypeError):
            validate_platform_name(input_value)


def test__validate_platform_name__2():
    """
    Tests whether `validate_platform_name` works as intended.
    
    Case: `ValueError`.
    """
    for input_value in (
        'a' * (PLATFORM_NAME_LENGTH_MAX + 1),
    ):
        with vampytest.assert_raises(ValueError):
            validate_platform_name(input_value)
