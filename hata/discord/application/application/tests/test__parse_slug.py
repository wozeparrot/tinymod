import vampytest

from ..fields import parse_slug


def _iter_options():
    yield {}, None
    yield {'slug': None}, None
    yield {'slug': ''}, None
    yield {'slug': 'https://orindance.party/'}, 'https://orindance.party/'


@vampytest._(vampytest.call_from(_iter_options()).returning_last())
def test__parse_slug(input_data):
    """
    Tests whether ``parse_slug`` works as intended.
    
    Parameters
    ----------
    input_data : `dict<str, object>`
        Data to parse from.
    
    Returns
    -------
    output : `None | str`
    """
    return parse_slug(input_data)
