import vampytest

from ..fields import put_pack_id_into


def test__put_pack_id_into():
    """
    Tests whether ``put_pack_id_into`` works as intended.
    """
    pack_id = 202301040006
    
    for input_value, defaults, expected_output in (
        (0, False, {}),
        (0, True, {'pack_id': None}),
        (pack_id, False, {'pack_id': str(pack_id)}),
    ):
        output = put_pack_id_into(input_value, {}, defaults)
        vampytest.assert_eq(output, expected_output)
