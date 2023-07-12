from hata import Client, Guild, InteractionEvent, Role
from hata.ext.slash import abort

TinyMod: Client
GUILD: Guild
ADMIN_ROLE: Role

@TinyMod.interactions(guild=GUILD, show_for_invoking_user_only=True)
async def join(client: Client, event):
  """Joins the voice channel that you are in."""
  if not event.user.has_role(ADMIN_ROLE): return
  voice_state = event.guild.voice_states.get(event.user.id, None)
  if not voice_state: abort("You must be in a voice channel to use this command.")

  try: await client.join_voice(voice_state.channel)
  except TimeoutError: abort("Timed out while connecting to voice channel.")

  return f"Joined {voice_state.channel:m}."

@TinyMod.interactions(guild=GUILD, show_for_invoking_user_only=True)
async def leave(client: Client, event):
  """Leaves the voice channel."""
  if not event.user.has_role(ADMIN_ROLE): return
  voice_client = client.voice_clients.get(event.guild.id, None)
  if not voice_client: abort("Not in a voice channel.")

  await voice_client.disconnect()

  return f"Left {voice_client.channel:m}."
