import vampytest

from ..fields import parse_enabled


def _iter_options():
    yield {}, True
    yield {'identity_enabled': False}, False
    yield {'identity_enabled': True}, True


@vampytest._(vampytest.call_from(_iter_options()).returning_last())
def test__parse_enabled(input_data):
    """
    Tests whether ``parse_enabled`` works as intended.
    
    Parameters
    ----------
    input_data : `dict<str, object>`
        Data to parse from.
    
    Returns
    -------
    output : `bool`
    """
    output = parse_enabled(input_data)
    vampytest.assert_instance(output, bool)
    return output
