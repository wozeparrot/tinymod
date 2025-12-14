from hata import Client, Guild, Role
from hata.ext.slash import InteractionResponse
from scarletio import get_event_loop

import logging
from pathlib import Path

TinyMod: Client
GUILD: Guild
ADMIN_ROLE: Role

REPO_DIR = Path("persist") / "tinygrad"
REPO = "https://github.com/tinygrad/tinygrad.git"

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

@TinyMod.interactions(guild=GUILD) # type: ignore
async def commit_table(client: Client, event):
  """weekly commits table."""
  if not event.user.has_role(ADMIN_ROLE): return
  message = yield "fetching repo..."
  await ensure_curr_repo()
  message = yield InteractionResponse(content="generating commit table...", message=message)

  # run python extra/weekly_commit_table.py and capture output
  logging.info("Generating commit table...")
  p = await get_event_loop().subprocess_shell("python extra/weekly_commits_table.py", cwd=REPO_DIR)
  stdout, stderr = await p.communicate()
  content = stdout.decode()

  yield InteractionResponse(content=content, message=message)
