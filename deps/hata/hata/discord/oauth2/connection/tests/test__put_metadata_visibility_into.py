import vampytest

from ..preinstanced import ConnectionVisibility

from ..fields import put_metadata_visibility_into


def test__put_metadata_visibility_into():
    """
    Tests whether ``put_metadata_visibility_into`` is working as intended.
    """
    for input_, defaults, expected_output in (
        (ConnectionVisibility.user_only, False, {}),
        (ConnectionVisibility.everyone, False, {'metadata_visibility': ConnectionVisibility.everyone.value}),
        (ConnectionVisibility.user_only, True, {'metadata_visibility': ConnectionVisibility.user_only.value}),
    ):
        data = put_metadata_visibility_into(input_, {}, defaults)
        vampytest.assert_eq(data, expected_output)
