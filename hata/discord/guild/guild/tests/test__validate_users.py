import vampytest

from ....user import User

from ..fields import validate_users


def _iter_options__passing():
    user_id_0 = 202404160004
    user_id_1 = 202404160005
    
    user_0 = User.precreate(user_id_0)
    user_1 = User.precreate(user_id_1)

    yield None, {}
    yield [], {}
    yield {}, {}
    yield [user_0], {user_id_0: user_0}
    yield [user_0, user_0], {user_id_0: user_0}
    yield [user_1, user_0], {user_id_0: user_0, user_id_1: user_1}
    yield [user_0, user_1], {user_id_0: user_0, user_id_1: user_1}
    yield {user_id_0: user_0}, {user_id_0: user_0}


def _iter_options__type_error():
    yield 12.6
    yield [12.6]
    yield {12.6: 12.6}


@vampytest._(vampytest.call_from(_iter_options__passing()).returning_last())
@vampytest._(vampytest.call_from(_iter_options__type_error()).raising(TypeError))
def test__validate_users(input_value):
    """
    Validates whether ``validate_users`` works as intended.
    
    Parameters
    ----------
    input_value : `object`
        The value to validate.
    
    Returns
    -------
    output : `dict<int, ClientUserBase>`
    
    Raises
    ------
    TypeError
    """
    return validate_users(input_value)
