import vampytest

from ....activity import Activity, ActivityType

from ..fields import validate_activity


def test__validate_activity__0():
    """
    Tests whether ``validate_activity`` works as intended.
    
    Case: passing.
    """
    activity = Activity('tsuki', activity_type = ActivityType.competing)
    
    for input_value, expected_output in (
        (activity, activity),
        (None, Activity()),
    ):
        output = validate_activity(input_value)
        vampytest.assert_eq(output, expected_output)


def test__validate_activity__1():
    """
    Tests whether ``validate_activity`` works as intended.
    
    Case: `TypeError`.
    """
    for input_value in (
        12.5,
    ):
        with vampytest.assert_raises(TypeError):
            validate_activity(input_value)
