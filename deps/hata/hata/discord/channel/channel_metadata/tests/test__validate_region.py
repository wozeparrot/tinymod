import vampytest

from ..fields import validate_region
from ..preinstanced import VoiceRegion


def test__validate_region__0():
    """
    Validates whether ``validate_region`` works as intended.
    
    Case: passing.
    """
    for input_value, expected_output in (
        (None, VoiceRegion.unknown),
        (VoiceRegion.brazil, VoiceRegion.brazil),
        (VoiceRegion.brazil.value, VoiceRegion.brazil)
    ):
        output = validate_region(input_value)
        vampytest.assert_is(output, expected_output)


def test__validate_region__1():
    """
    Validates whether ``validate_region`` works as intended.
    
    Case: `TypeError`.
    """
    for input_value in (
        12.6,
    ):
        with vampytest.assert_raises(TypeError):
            validate_region(input_value)
