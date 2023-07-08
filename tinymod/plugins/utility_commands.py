from hata import Client, Guild, Role
from hata.ext.slash import abort

TinyMod: Client
GUILD: Guild

ADMIN_ROLE = Role.precreate(1068980562477465670)

@TinyMod.interactions(guild=GUILD,show_for_invoking_user_only=True)
async def vcjump(client, event, channel: ("channel_id", "Channel ID to jump to")):
  if not channel: abort("You must provide a channel ID to jump to.")
  if not isinstance(channel, int): abort("Channel ID must be an integer.")

  # ensure that user is an admin
  if not event.user.has_role(ADMIN_ROLE): abort("You must be an admin to use this command.")

  # ensure that user is in a voice channel
  voice_state = event.guild.voice_states.get(event.user.id, None)
  if not voice_state: abort("You must be in a voice channel to use this command.")

  # get all members in the voice channel
  for user in voice_state.channel.iter_voice_users():
    await client.user_voice_move(user, (event.guild.id, channel))

  return f"Moved all users in {voice_state.channel:m} to <#{channel}>."
