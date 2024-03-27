import vampytest

from ..constants import VALUE_LENGTH_MAX
from ..fields import validate_value


def test__validate_value__0():
    """
    Tests whether `validate_value` works as intended.
    
    Case: passing.
    """
    for input_value, expected_output in (
        (None, ''),
        ('a', 'a'),
    ):
        output = validate_value(input_value)
        vampytest.assert_eq(output, expected_output)


def test__validate_value__1():
    """
    Tests whether `validate_value` works as intended.
    
    Case: `ValueError`.
    """
    for input_value in (
        'a' * (VALUE_LENGTH_MAX + 1),
    ):
        with vampytest.assert_raises(ValueError):
            validate_value(input_value)


def test__validate_value__2():
    """
    Tests whether `validate_value` works as intended.
    
    Case: `TypeError`.
    """
    for input_value in (
        12.6,
    ):
        with vampytest.assert_raises(TypeError):
            validate_value(input_value)
