import vampytest

from ..fields import validate_flags
from ..flags import RoleFlag


def _iter_options__passing():
    yield None, RoleFlag(0)
    yield 1, RoleFlag(1)
    yield RoleFlag(1), RoleFlag(1)


def _iter_options__type_error():
    yield 'a'
    yield 12.6


@vampytest._(vampytest.call_from(_iter_options__passing()).returning_last())
@vampytest._(vampytest.call_from(_iter_options__type_error()).raising(TypeError))
def test__validate_flags(input_value):
    """
    Tests whether `validate_flags` works as intended.
    
    Parameters
    ----------
    input_value : `object`
        The value to validate.
    
    Returns
    -------
    value : ``RoleFlag``
    
    Raises
    ------
    TypeError
    """
    output = validate_flags(input_value)
    vampytest.assert_instance(output, RoleFlag)
    return output
