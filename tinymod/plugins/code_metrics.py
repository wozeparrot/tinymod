from hata import Client, Guild, Role, Channel, Message
from hata.ext.slash import InteractionResponse
from scarletio import get_event_loop
import prettytable
from prettytable import MARKDOWN

import sys, logging, re, importlib.util, os
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

_sz = None
def load_sz():
  """Loads tinygrad's own sz.py from the cloned repo so we reuse its line counting."""
  global _sz
  if _sz is None:
    repo = str(REPO_DIR.resolve())
    if repo not in sys.path: sys.path.insert(0, repo)
    spec = importlib.util.spec_from_file_location("tinygrad_sz", REPO_DIR / "sz.py")
    _sz = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(_sz)
  return _sz

async def get_curr_metrics():
  await ensure_curr_repo()
  return load_sz().gen_stats(str(REPO_DIR))

MAX_LINE_REGEX = re.compile(r"MAX_LINE_COUNT=(\d+)")
async def get_curr_max_lines():
  await ensure_curr_repo()

  with (REPO_DIR / ".github" / "workflows" / "test.yml").open("r") as f:
    for line in f:
      match = MAX_LINE_REGEX.search(line)
      if match is not None: return int(match.group(1))
  return 0

@TinyMod.interactions(guild=GUILD) # type: ignore
async def line_count(client: Client, event):
  """Displays the total line count and the line count per file."""
  message = yield "calculating metrics..."

  metrics = await get_curr_metrics()
  total_line_count = sum(row[1] for row in metrics)
  sorted_metrics = sorted(metrics, key=lambda x: x[1], reverse=True)

  table = prettytable.PrettyTable()
  table.set_style(MARKDOWN)
  table.field_names = ["File", "Line Count"]
  def render(): return f"# Total line count: {total_line_count}\n\n**Largest Files:**\n```{table.get_string()}```"
  for path, line_count, _ in sorted_metrics:
    table.add_row([path, line_count])
    if len(render()) > 1990:
      table.del_row(len(table.rows) - 1)
      break

  yield InteractionResponse(content=render(), message=message)

LINE_COUNT_CHANNEL = Channel.precreate(os.getenv("LINE_COUNT_CHANNEL_ID", 1068991125353939066))
@TinyMod.interactions(guild=GUILD, show_for_invoking_user_only=True) # type: ignore
async def update_line_count(client: Client, event):
  """Updates the line count metrics."""
  if not event.user.has_role(ADMIN_ROLE): return
  message = yield "updating metrics..."

  metrics = await get_curr_metrics()
  total_line_count = sum(row[1] for row in metrics)
  max_line_count = await get_curr_max_lines()
  free_lines = max_line_count - total_line_count

  # update the topic
  await client.channel_edit(LINE_COUNT_CHANNEL, topic=f"Current line count: {total_line_count} <= {max_line_count} ({free_lines} free)")

  yield InteractionResponse(content=f"Updated line count: {total_line_count}", message=message)

CI_CHANNEL_ID = 1068993556905218128
GITHUB_WEBHOOK_ID = 1068993579520884826
@TinyMod.events # type: ignore
async def message_create(client: Client, message: Message):
  if message.channel.id != CI_CHANNEL_ID: return
  if message.author.id != GITHUB_WEBHOOK_ID: return

  # check if it is a commit to master
  if message.embeds is None: return
  if len(message.embeds) < 1: return
  embed = message.embeds[0]
  if "[tinygrad:master]" not in embed.title: return
  if "new commit" not in embed.title: return

  # update the line count
  logging.info("Updating line count topic...")
  metrics = await get_curr_metrics()
  total_line_count = sum(row[1] for row in metrics)
  max_line_count = await get_curr_max_lines()
  free_lines = max_line_count - total_line_count

  # update the topic
  await client.channel_edit(LINE_COUNT_CHANNEL, topic=f"Current line count: {total_line_count} <= {max_line_count} ({free_lines} free)")

  logging.info("Updated line count topic.")
