from hata import Client, Guild, Role, LocalAudio
from hata.ext.slash import InteractionResponse, abort

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

@TinyMod.interactions(guild=GUILD, show_for_invoking_user_only=True)
async def tts(client: Client, event, text: ("str", "Text to say.")):
  """Send a TTS message to the voice channel."""
  voice_client = client.voice_clients.get(event.guild.id, None)
  if not voice_client: abort("Not in a voice channel.")

  message = yield InteractionResponse("Generating audio...")

  async with client.http.post("http://127.0.0.1:8000", data=text) as response:
    if response.status != 200: abort("Failed to generate audio.")
    else: await response.json()
    yield InteractionResponse("Generated audio.", message=message)

  audio = await LocalAudio("/home/woze/dev/tinygrad/test.opus")
  voice_client.append(audio)

  yield InteractionResponse(f"Sent TTS message to {voice_client.channel:m}.", message=message)
