from hata import Client, Guild, Role, Channel, Message
from hata.ext.slash import InteractionResponse
from scarletio import get_event_loop
import prettytable
from prettytable import MARKDOWN

import token, tokenize
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
  print("Ensuring current repo...")
  if not REPO_DIR.exists():
    p = await get_event_loop().subprocess_shell(f"git clone {REPO}", cwd=REPO_DIR.parent)
    await p.communicate()
  else:
    await git_cmd("fetch")
    await git_cmd("reset", "--hard", "origin/master")

TOKEN_WHITELIST = [token.OP, token.NAME, token.NUMBER, token.STRING]
PATH_BLACKLIST = ["autogen"]
async def get_curr_metrics():
  await ensure_curr_repo()

  metrics = {}
  for path in (REPO_DIR / "tinygrad").rglob("*.py"):
    if any(blacklist in str(path) for blacklist in PATH_BLACKLIST): continue
    with path.open("r") as f:
      tokens = [t for t in tokenize.generate_tokens(f.readline) if t.type in TOKEN_WHITELIST]
    line_count = len(set([x for t in tokens for x in range(t.start[0], t.end[0]+1)]))
    metrics[str(path.relative_to(REPO_DIR / "tinygrad"))] = {"line_count": line_count}
  return metrics

@TinyMod.interactions(guild=GUILD) # type: ignore
async def line_count(client: Client, event):
  """Displays the total line count and the line count per file."""
  message = yield "calculating metrics..."

  metrics = await get_curr_metrics()
  total_line_count = sum(m["line_count"] for m in metrics.values())
  sorted_metrics = sorted(metrics.items(), key=lambda x: x[1]["line_count"], reverse=True)[:37]

  table = prettytable.PrettyTable()
  table.set_style(MARKDOWN)
  table.field_names = ["File", "Line Count"]
  for path, data in sorted_metrics: table.add_row([path, data["line_count"]])

  yield InteractionResponse(content=f"# Total line count: {total_line_count}\n\n**Largest Files:**\n```{table.get_string()}```", message=message)

LINE_COUNT_CHANNEL = Channel.precreate(1068991125353939066)
@TinyMod.interactions(guild=GUILD, show_for_invoking_user_only=True) # type: ignore
async def update_line_count(client: Client, event):
  """Updates the line count metrics."""
  if not event.user.has_role(ADMIN_ROLE): return
  message = yield "updating metrics..."

  metrics = await get_curr_metrics()
  total_line_count = sum(m["line_count"] for m in metrics.values())
  await client.channel_edit(LINE_COUNT_CHANNEL, topic=f"Current line count: {total_line_count}")

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
  print("Updating line count topic...")
  metrics = await get_curr_metrics()
  total_line_count = sum(m["line_count"] for m in metrics.values())
  await client.channel_edit(LINE_COUNT_CHANNEL, topic=f"Current line count: {total_line_count}")
  print("Updated line count topic.")
