import sys, os, logging
sys.path.insert(0, "./deps/hata")
sys.path.insert(0, "./deps/scarletio")
logging.basicConfig(level=logging.DEBUG if os.getenv("DEBUG") else logging.INFO, format="%(asctime)s [%(levelname)s] <%(filename)s:%(funcName)s> %(message)s")

from dotenv import load_dotenv
load_dotenv()

from hata import Activity, ActivityType, Client, Guild, Role, wait_for_interruption
from hata.ext.plugin_loader import add_default_plugin_variables, load_all_plugin, register_plugin
from hata.ext.plugin_auto_reloader.utils import start_auto_reloader, stop_auto_reloader, warn_auto_reloader_availability
from hata.ext.slash import setup_ext_slash

from scarletio import get_or_create_event_loop, sleep

from stats.api import Api

# Presetup some stuff
assert (TOKEN := os.getenv("TOKEN")), 'Environment variable "TOKEN" not found. Add it to your local .env file.'
GUILD = Guild.precreate(os.getenv("GUILD_ID", 1068976834382925865))
ADMIN_ROLE = Role.precreate(os.getenv("ADMIN_ROLE_ID", 1068980562477465670))

# Create bot
TinyMod = Client(
  TOKEN,
  activity=Activity("you...", activity_type=ActivityType.watching),
)
slash = setup_ext_slash(TinyMod, use_default_exception_handler=False)

@TinyMod.events
async def ready(client: Client):
  logging.info(f"{client:f} logged in.")

@slash.error
async def slash_error(client: Client, event, *_):
  try:
    await client.interaction_response_message_create(event, "Something broke! Ping <@359455849812328449>", show_for_invoking_user_only=True)
  except: pass
  return False

# Load plugins
add_default_plugin_variables(TinyMod=TinyMod, GUILD=GUILD, ADMIN_ROLE=ADMIN_ROLE)
register_plugin("plugins")
load_all_plugin()

LOOP = get_or_create_event_loop()
async def main():
  # Start auto reloader
  warn_auto_reloader_availability()
  start_auto_reloader()

  # Start bot
  TinyMod.start()
  logging.info("Bot started.")

  # start stats api
  stats_api = Api()
  await stats_api.start()
  logging.info("Stats API started.")
LOOP.run(main())
wait_for_interruption()
