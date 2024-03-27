from datetime import datetime as DateTime

import vampytest

from ..fields import validate_ends_at


def _iter_options():
    ends_at = DateTime(2016, 5, 14)
    
    yield None, None
    yield ends_at, ends_at


@vampytest._(vampytest.call_from(_iter_options()).returning_last())
def test__validate_ends_at__passing(input_value):
    """
    Tests whether ``validate_ends_at`` works as intended.
    
    Case: passing.
    
    Parameters
    ----------
    input_value : `object`
        The value to validate.
    
    Returns
    -------
    output : `None | DateTime`
    """
    return validate_ends_at(input_value)


@vampytest.raising(TypeError)
@vampytest.call_with(12.6)
def test__validate_ends_at__type_error(input_value):
    """
    Tests whether ``validate_ends_at`` works as intended.
    
    Case: `TypeError`.
    
    Parameters
    ----------
    input_value : `object`
        The value to validate.
    
    Raises
    ------
    TypeError
    """
    validate_ends_at(input_value)
