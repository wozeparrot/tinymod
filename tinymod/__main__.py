from dotenv import load_dotenv
load_dotenv()

from hata import Activity, ActivityType, Client, Guild, wait_for_interruption
from hata.ext.plugin_loader import add_default_plugin_variables, load_all_plugin, register_plugin
from hata.ext.slash import setup_ext_slash

import os

# Presetup some stuff
GUILD = Guild.precreate(1068976834382925865)

# Create bot
TinyMod = Client(os.environ["TOKEN"], activity=Activity("you...", activity_type=ActivityType.watching))
slash = setup_ext_slash(TinyMod, use_default_exception_handler=False)

@TinyMod.events
async def ready(client: Client):
  print(f"{client:f} logged in.")

@slash.error
async def slash_error(client: Client, event, *_):
  await client.interaction_response_message_create(event, "Something broke! Ping <@359455849812328449>")
  return False

# Load plugins
add_default_plugin_variables(TinyMod=TinyMod, GUILD=GUILD)
register_plugin("plugins")
load_all_plugin()

# Start bot
TinyMod.start()

wait_for_interruption()
