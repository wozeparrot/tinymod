from dotenv import load_dotenv
load_dotenv()

from hata import Client, Guild, wait_for_interruption
from hata.ext.plugin_loader import add_default_plugin_variables, load_all_plugin, register_plugin

import os

# Presetup some stuff
GUILD = Guild.precreate(1068976834382925865)

# Create bot
TinyMod = Client(os.environ["TOKEN"], extensions=["slash"])

@TinyMod.events
async def ready(client: Client):
  print(f"{client:f} logged in.")

# Load plugins
add_default_plugin_variables(TinyMod=TinyMod, GUILD=GUILD)
register_plugin("plugins")
load_all_plugin()

# Start bot
TinyMod.start()

wait_for_interruption()
