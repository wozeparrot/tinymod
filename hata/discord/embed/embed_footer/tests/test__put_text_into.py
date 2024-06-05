import vampytest

from ..fields import put_text_into


def _iter_options():
    yield None, False, {'text': ''}
    yield None, True, {'text': ''}
    yield 'a', False, {'text': 'a'}
    yield 'a', True, {'text': 'a'}


@vampytest._(vampytest.call_from(_iter_options()).returning_last())
def test__put_text_into(input_value, defaults):
    """
    Tests whether ``put_text_into`` works as intended.
    
    Parameters
    ----------
    input_value : `None`, `str`
        Value to put into data.
    defaults : `bool`
        Whether values of their default value should be included as well.
    
    Returns
    -------
    output : `dict<str, object>`
    """
    return put_text_into(input_value, {}, defaults)
