import vampytest

from ....localization import Locale

from ..application_command_option_choice import ApplicationCommandOptionChoice


def test__ApplicationCommandOptionChoice__repr():
    """
    Tests whether ``ApplicationCommandOptionChoice.__repr__`` works as intended.
    """
    name = 'satori'
    name_localizations = {
        Locale.german: 'koishi',
    }
    value = 456
    
    application_command_option_choice = ApplicationCommandOptionChoice(
        name = name,
        name_localizations = name_localizations,
        value = value,
    )
    
    vampytest.assert_instance(repr(application_command_option_choice), str)


def test__ApplicationCommandOptionChoice__hash():
    """
    Tests whether ``ApplicationCommandOptionChoice.__hash__`` works as intended.
    """
    name = 'satori'
    name_localizations = {
        Locale.german: 'koishi',
    }
    value = 456
    
    application_command_option_choice = ApplicationCommandOptionChoice(
        name = name,
        name_localizations = name_localizations,
        value = value,
    )
    
    vampytest.assert_instance(hash(application_command_option_choice), int)


def test__ApplicationCommandOptionChoice__eq():
    """
    Tests whether ``ApplicationCommandOptionChoice.__eq__`` works as intended.
    """
    name = 'satori'
    name_localizations = {
        Locale.german: 'koishi',
    }
    value = 456
    
    keyword_parameters = {
        'name': name,
        'name_localizations': name_localizations,
        'value': value,
    }
    
    application_command_option_choice = ApplicationCommandOptionChoice(**keyword_parameters)
    
    vampytest.assert_eq(application_command_option_choice, application_command_option_choice)
    vampytest.assert_ne(application_command_option_choice, object())
    
    for field_name, field_value in (
        ('name', 'komeiji'),
        ('name_localizations', None),
        ('value', 12.6)
    ):
        test_application_command_option_choice = ApplicationCommandOptionChoice(
            **{**keyword_parameters, field_name: field_value}
        )
        vampytest.assert_ne(application_command_option_choice, test_application_command_option_choice)


def test__ApplicationCommandOptionChoice__len__0():
    """
    Tests whether ``ApplicationCommandOptionChoice.__len__`` only counts the longest name's length and not all's together.
    
    Case: The longest is a localization.
    """
    name_1 = 'hi'
    name_2 = 'hoi'
    name_3 = 'halo'
    
    application_command_option_choice = ApplicationCommandOptionChoice(
        name_1,
        12.6,
        name_localizations = {
            Locale.thai: name_2,
            Locale.czech: name_3,
        },
    )
    
    expected_length = max(
        len(name) for name in (name_1, name_2, name_3)
    )
    
    vampytest.assert_eq(len(application_command_option_choice), expected_length)


def test__ApplicationCommandOptionChoice__len__1():
    """
    Tests whether ``ApplicationCommandOptionChoice.__len__`` only counts the longest name's length and not all's together.
    
    Case: The longest is the name itself.
    """
    name_1 = 'hi'
    name_2 = 'hoi'
    name_3 = 'halo'
    
    application_command_option_choice = ApplicationCommandOptionChoice(
        name_3,
        12.6,
        name_localizations = {
            Locale.thai: name_1,
            Locale.czech: name_2,
        },
    )
    
    expected_length = max(
        len(name) for name in (name_1, name_2, name_3)
    )
    
    vampytest.assert_eq(len(application_command_option_choice), expected_length)


def test__ApplicationCommandOptionChoice__hash__1():
    """
    Tests whether ``ApplicationCommandOptionChoice.__hash__`` works as intended.
    """
    application_command_option_choice = ApplicationCommandOptionChoice(
        'hello',
        'hell',
        name_localizations = {
            Locale.thai: 'everybody',
        },
    )
    
    vampytest.assert_instance(hash(application_command_option_choice), int)
