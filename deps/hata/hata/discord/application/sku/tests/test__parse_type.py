import vampytest

from ..fields import parse_type
from ..preinstanced import SKUType


def _iter_options():
    yield {}, SKUType.none
    yield {'type': SKUType.consumable.value}, SKUType.consumable


@vampytest._(vampytest.call_from(_iter_options()).returning_last())
def test__parse_type(input_data):
    """
    Tests whether ``parse_type`` works as intended.
    
    Parameters
    ----------
    input_data : `dict<str, object>`
        Input data.
    
    Returns
    -------
    output : ``SKUType``
    """
    output = parse_type(input_data)
    vampytest.assert_instance(output, SKUType)
    return output
