__all__ = ()


MAX_PRESENCES_DEFAULT = 0
MAX_USERS_DEFAULT = 250000 # Most already has 500000 by default
MAX_STAGE_CHANNEL_VIDEO_USERS_DEFAULT = 50
MAX_VOICE_CHANNEL_VIDEO_USERS_DEFAULT = 25

NAME_LENGTH_MIN = 2
NAME_LENGTH_MAX = 100

AFK_TIMEOUT_DEFAULT = 0
AFK_TIMEOUT_OPTIONS = frozenset((0, 60, 300, 900, 1800, 3600),)

DESCRIPTION_LENGTH_MAX = 120

LARGE_GUILD_LIMIT = 250 # can be between 50 and 250


# State flags

GUILD_STATE_MASK_SOUNDBOARD_SOUNDS_CACHED = 1 << 0
GUILD_STATE_MASK_CACHE_BOOSTERS = 1 << 1

GUILD_STATE_MASK_CACHE_ALL = GUILD_STATE_MASK_CACHE_BOOSTERS

# Constants for events

EMOJI_EVENT_NONE = 0
EMOJI_EVENT_CREATE = 1
EMOJI_EVENT_DELETE = 2
EMOJI_EVENT_UPDATE = 3


SOUNDBOARD_SOUND_EVENT_NONE = 0
SOUNDBOARD_SOUND_EVENT_CREATE = 1
SOUNDBOARD_SOUND_EVENT_DELETE = 2
SOUNDBOARD_SOUND_EVENT_UPDATE = 3


STICKER_EVENT_NONE = 0
STICKER_EVENT_CREATE = 1
STICKER_EVENT_DELETE = 2
STICKER_EVENT_UPDATE = 3


VOICE_STATE_EVENT_NONE = 0
VOICE_STATE_EVENT_JOIN = 1
VOICE_STATE_EVENT_LEAVE = 2
VOICE_STATE_EVENT_UPDATE = 3
VOICE_STATE_EVENT_MOVE = 4
