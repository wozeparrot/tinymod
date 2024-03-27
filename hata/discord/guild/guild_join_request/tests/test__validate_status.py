import vampytest

from ..fields import validate_status
from ..preinstanced import GuildJoinRequestStatus


def test__validate_status__0():
    """
    Validates whether ``validate_status`` works as intended.
    
    Case: passing.
    """
    for input_value, expected_output in (
        (GuildJoinRequestStatus.pending, GuildJoinRequestStatus.pending),
        (GuildJoinRequestStatus.pending.value, GuildJoinRequestStatus.pending)
    ):
        output = validate_status(input_value)
        vampytest.assert_is(output, expected_output)


def test__validate_status__1():
    """
    Validates whether ``validate_status`` works as intended.
    
    Case: `TypeError`.
    """
    for input_value in (
        12.6,
    ):
        with vampytest.assert_raises(TypeError):
            validate_status(input_value)
