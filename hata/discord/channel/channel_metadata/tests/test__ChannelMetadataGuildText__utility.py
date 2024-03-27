import vampytest

from ...permission_overwrite import PermissionOverwrite, PermissionOverwriteTargetType

from ..guild_text import ChannelMetadataGuildText

from .test__ChannelMetadataGuildText__constructor import _assert_fields_set


def test__ChannelMetadataGuildText__copy():
    """
    Tests whether ``ChannelMetadataGuildText.copy` works as intended.
    """
    name = 'alice'
    parent_id = 202304130042
    permission_overwrites = [
        PermissionOverwrite(202304130043, target_type = PermissionOverwriteTargetType.user)
    ]
    position = 7
    default_thread_auto_archive_after = 86400
    default_thread_slowmode = 60
    nsfw = True
    slowmode = 30
    topic = 'rin'
    
    channel_metadata = ChannelMetadataGuildText(
        name = name,
        parent_id = parent_id,
        permission_overwrites = permission_overwrites,
        position = position,
        default_thread_auto_archive_after = default_thread_auto_archive_after,
        default_thread_slowmode = default_thread_slowmode,
        nsfw = nsfw,
        slowmode = slowmode,
        topic = topic,
    )
    
    copy = channel_metadata.copy()
    _assert_fields_set(copy)
    vampytest.assert_is_not(copy, channel_metadata)
    
    vampytest.assert_eq(copy, channel_metadata)


def test__ChannelMetadataGuildText__copy_with__0():
    """
    Tests whether ``ChannelMetadataGuildText.copy_with` works as intended.
    
    Case: No fields.
    """
    name = 'alice'
    parent_id = 202304130044
    permission_overwrites = [
        PermissionOverwrite(202304130045, target_type = PermissionOverwriteTargetType.user)
    ]
    position = 7
    default_thread_auto_archive_after = 86400
    default_thread_slowmode = 60
    nsfw = True
    slowmode = 30
    topic = 'rin'
    
    channel_metadata = ChannelMetadataGuildText(
        name = name,
        parent_id = parent_id,
        permission_overwrites = permission_overwrites,
        position = position,
        default_thread_auto_archive_after = default_thread_auto_archive_after,
        default_thread_slowmode = default_thread_slowmode,
        nsfw = nsfw,
        slowmode = slowmode,
        topic = topic,
    )
    
    copy = channel_metadata.copy_with()
    _assert_fields_set(copy)
    vampytest.assert_is_not(copy, channel_metadata)
    
    vampytest.assert_eq(copy, channel_metadata)


def test__ChannelMetadataGuildText__copy_with__1():
    """
    Tests whether ``ChannelMetadataGuildText.copy_with` works as intended.
    
    Case: All fields.
    """
    old_name = 'alice'
    old_parent_id = 202304130046
    old_permission_overwrites = [
        PermissionOverwrite(202304130047, target_type = PermissionOverwriteTargetType.user)
    ]
    old_position = 7
    old_default_thread_auto_archive_after = 86400
    old_default_thread_slowmode = 60
    old_nsfw = True
    old_slowmode = 30
    old_topic = 'rin'
    
    new_name = 'emotion'
    new_parent_id = 202304130048
    new_permission_overwrites = [
        PermissionOverwrite(202304130049, target_type = PermissionOverwriteTargetType.role)
    ]
    new_position = 5
    new_default_thread_auto_archive_after = 3600
    new_default_thread_slowmode = 69
    new_nsfw = False
    new_slowmode = 33
    new_topic = 'orin'
    
    channel_metadata = ChannelMetadataGuildText(
        name = old_name,
        parent_id = old_parent_id,
        permission_overwrites = old_permission_overwrites,
        position = old_position,
        default_thread_auto_archive_after = old_default_thread_auto_archive_after,
        default_thread_slowmode = old_default_thread_slowmode,
        nsfw = old_nsfw,
        slowmode = old_slowmode,
        topic = old_topic,
    )
    
    copy = channel_metadata.copy_with(
        name = new_name,
        parent_id = new_parent_id,
        permission_overwrites = new_permission_overwrites,
        position = new_position,
        default_thread_auto_archive_after = new_default_thread_auto_archive_after,
        default_thread_slowmode = new_default_thread_slowmode,
        nsfw = new_nsfw,
        slowmode = new_slowmode,
        topic = new_topic,
    )
    _assert_fields_set(copy)
    vampytest.assert_is_not(copy, channel_metadata)
    
    vampytest.assert_eq(copy.name, new_name)
    vampytest.assert_eq(copy.parent_id, new_parent_id)
    vampytest.assert_eq(
        copy.permission_overwrites,
        {permission_overwrite.target_id: permission_overwrite for permission_overwrite in new_permission_overwrites},
    )
    vampytest.assert_eq(copy.position, new_position)
    vampytest.assert_eq(copy.default_thread_auto_archive_after, new_default_thread_auto_archive_after)
    vampytest.assert_eq(copy.default_thread_slowmode, new_default_thread_slowmode)
    vampytest.assert_eq(copy.nsfw, new_nsfw)
    vampytest.assert_eq(copy.slowmode, new_slowmode)
    vampytest.assert_eq(copy.topic, new_topic)


def test__ChannelMetadataGuildText__copy_with_keyword_parameters__0():
    """
    Tests whether ``ChannelMetadataGuildText.copy_with_keyword_parameters` works as intended.
    
    Case: No fields.
    """
    name = 'alice'
    parent_id = 202304130050
    permission_overwrites = [
        PermissionOverwrite(202304130051, target_type = PermissionOverwriteTargetType.user)
    ]
    position = 7
    default_thread_auto_archive_after = 86400
    default_thread_slowmode = 60
    nsfw = True
    slowmode = 30
    topic = 'rin'
    
    channel_metadata = ChannelMetadataGuildText(
        name = name,
        parent_id = parent_id,
        permission_overwrites = permission_overwrites,
        position = position,
        default_thread_auto_archive_after = default_thread_auto_archive_after,
        default_thread_slowmode = default_thread_slowmode,
        nsfw = nsfw,
        slowmode = slowmode,
        topic = topic,
    )
    
    keyword_parameters = {}
    copy = channel_metadata.copy_with_keyword_parameters(keyword_parameters)
    _assert_fields_set(copy)
    vampytest.assert_is_not(copy, channel_metadata)
    vampytest.assert_eq(keyword_parameters, {})
    
    vampytest.assert_eq(copy, channel_metadata)


def test__ChannelMetadataGuildText__copy_with_keyword_parameters__1():
    """
    Tests whether ``ChannelMetadataGuildText.copy_with_keyword_parameters` works as intended.
    
    Case: All fields.
    """
    old_name = 'alice'
    old_parent_id = 202304130052
    old_permission_overwrites = [
        PermissionOverwrite(202304130053, target_type = PermissionOverwriteTargetType.user)
    ]
    old_position = 7
    old_default_thread_auto_archive_after = 86400
    old_default_thread_slowmode = 60
    old_nsfw = True
    old_slowmode = 30
    old_topic = 'rin'
    
    new_name = 'emotion'
    new_parent_id = 202304130054
    new_permission_overwrites = [
        PermissionOverwrite(202304130055, target_type = PermissionOverwriteTargetType.role)
    ]
    new_position = 5
    new_default_thread_auto_archive_after = 3600
    new_default_thread_slowmode = 69
    new_nsfw = False
    new_slowmode = 33
    new_topic = 'orin'
    
    channel_metadata = ChannelMetadataGuildText(
        name = old_name,
        parent_id = old_parent_id,
        permission_overwrites = old_permission_overwrites,
        position = old_position,
        default_thread_auto_archive_after = old_default_thread_auto_archive_after,
        default_thread_slowmode = old_default_thread_slowmode,
        nsfw = old_nsfw,
        slowmode = old_slowmode,
        topic = old_topic,
    )
    
    keyword_parameters = {
        'name': new_name,
        'parent_id': new_parent_id,
        'permission_overwrites': new_permission_overwrites,
        'position': new_position,
        'default_thread_auto_archive_after': new_default_thread_auto_archive_after,
        'default_thread_slowmode': new_default_thread_slowmode,
        'nsfw': new_nsfw,
        'slowmode': new_slowmode,
        'topic': new_topic,
    }
    
    copy = channel_metadata.copy_with_keyword_parameters(keyword_parameters)
    _assert_fields_set(copy)
    vampytest.assert_is_not(copy, channel_metadata)
    vampytest.assert_eq(keyword_parameters, {})
    
    vampytest.assert_eq(copy.name, new_name)
    vampytest.assert_eq(copy.parent_id, new_parent_id)
    vampytest.assert_eq(
        copy.permission_overwrites,
        {permission_overwrite.target_id: permission_overwrite for permission_overwrite in new_permission_overwrites},
    )
    vampytest.assert_eq(copy.position, new_position)
    vampytest.assert_eq(copy.default_thread_auto_archive_after, new_default_thread_auto_archive_after)
    vampytest.assert_eq(copy.default_thread_slowmode, new_default_thread_slowmode)
    vampytest.assert_eq(copy.nsfw, new_nsfw)
    vampytest.assert_eq(copy.slowmode, new_slowmode)
    vampytest.assert_eq(copy.topic, new_topic)
