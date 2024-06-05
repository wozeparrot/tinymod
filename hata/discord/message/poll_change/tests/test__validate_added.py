import vampytest

from ....poll import Poll

from ..fields import validate_added


def _iter_options__passing():
    poll = Poll(duration = 3600)
    
    yield poll, poll
    yield None, None


def _iter_options__type_error():
    yield 12.6


@vampytest._(vampytest.call_from(_iter_options__passing()).returning_last())
@vampytest._(vampytest.call_from(_iter_options__type_error()).raising(TypeError))
def test__validate_added__passing(input_value):
    """
    Tests whether `validate_added` works as intended.
    
    Parameters
    ----------
    input_value : `object`
        Input value to test with.
    
    Returns
    -------
    output : `None`, ``Poll``
    
    Raises
    ------
    TypeError
    """
    return validate_added(input_value)
