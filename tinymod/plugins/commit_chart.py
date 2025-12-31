from hata import Client, Guild, Channel, Role, KOKORO
from hata.ext.slash import InteractionResponse
from scarletio import get_event_loop

import logging, os
from pathlib import Path
from datetime import datetime, timezone

TinyMod: Client
GUILD: Guild
ADMIN_ROLE: Role

REPO_DIR = Path("persist") / "tinygrad"
REPO = "https://github.com/tinygrad/tinygrad.git"

CHANNEL = Channel.precreate(os.getenv("CC_CHANNEL_ID", 1215699423527698483))

# should post every saturday at 12:00 AM PST
POST_TIME = {
  "weekday": 5,
  "hour": 8,
  "minute": 0,
}
LAST_POST_DATE = None

async def git_cmd(*args):
  p = await get_event_loop().subprocess_shell(f"git {' '.join(args)}", cwd=REPO_DIR)
  return await p.communicate()

async def ensure_curr_repo():
  logging.info("Ensuring current repo...")
  if not REPO_DIR.exists():
    p = await get_event_loop().subprocess_shell(f"git clone {REPO}", cwd=REPO_DIR.parent)
    await p.communicate()
  else:
    await git_cmd("fetch")
    await git_cmd("reset", "--hard", "origin/master")

async def get_commit_table():
  await ensure_curr_repo()

  # run python extra/weekly_commit_table.py and capture output
  logging.info("Generating commit table...")
  p = await get_event_loop().subprocess_shell("python extra/weekly_commits_table.py", cwd=REPO_DIR)
  stdout, _ = await p.communicate()
  content = stdout.decode()

  return content

@TinyMod.interactions(guild=GUILD) # type: ignore
async def commit_table(client: Client, event):
  """weekly commits table."""
  if not event.user.has_role(ADMIN_ROLE): return
  message = yield "generating commit table..."

  content = await get_commit_table()

  yield InteractionResponse(content=content, message=message)

loop_handle = None
@TinyMod.events # type: ignore
async def ready(client: Client):
  global loop_handle
  if loop_handle is not None: return
  step_loop()

@TinyMod.events # type: ignore
async def shutdown(client: Client):
  global loop_handle
  if loop_handle is None: return
  loop_handle.cancel()
  loop_handle = None

def step_loop():
  global loop_handle
  loop_handle = KOKORO.call_after(10, step_loop)
  KOKORO.create_task(post_commit_table_on_time())

async def post_commit_table_on_time():
  global LAST_POST_DATE
  now = datetime.now(timezone.utc)

  is_scheduled_time = (
    now.weekday() == POST_TIME["weekday"] and
    now.hour == POST_TIME["hour"] and
    now.minute == POST_TIME["minute"]
  )

  if is_scheduled_time and LAST_POST_DATE != now.date():
    LAST_POST_DATE = now.date()

    content = await get_commit_table()

    TinyMod.message_create(CHANNEL, content=content)
