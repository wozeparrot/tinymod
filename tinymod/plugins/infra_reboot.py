from hata import Client, Embed, Guild, Channel, Role
from hata.ext.slash import abort, InteractionResponse
from scarletio import get_event_loop
from subprocess import STDOUT

import os, json, logging, time

TinyMod: Client
GUILD: Guild
ADMIN_ROLE: Role

INFRA_DIR = os.environ.get("INFRA_DIR", "")
TINYBOX_ACCESS_CHANNEL = Channel.precreate(int(os.getenv("TINYBOX_ACCESS_CHANNEL_ID", 1212791472731201666)))
EMPLOYEE_ROLE = Role.precreate(int(os.getenv("EMPLOYEE_ROLE_ID", 1069237221384802374)))
SCRIPT = os.path.join(INFRA_DIR, "extra", "reboot_control.py") if INFRA_DIR else ""

async def run_script(*args):
  p = await get_event_loop().subprocess_exec("python", SCRIPT, *args)
  stdout, stderr = await p.communicate()
  return p.return_code, stdout.decode(), stderr.decode()

BOX_LIST_CACHE = None
BOX_LIST_CACHE_TIME = 0
BOX_LIST_TTL = 300

async def get_box_list():
  global BOX_LIST_CACHE, BOX_LIST_CACHE_TIME
  if BOX_LIST_CACHE is not None and time.monotonic() - BOX_LIST_CACHE_TIME < BOX_LIST_TTL:
    return BOX_LIST_CACHE, None
  rc, stdout, stderr = await run_script("--list", "--json")
  if rc != 0: return None, stderr
  BOX_LIST_CACHE = json.loads(stdout)
  BOX_LIST_CACHE_TIME = time.monotonic()
  return BOX_LIST_CACHE, None

@TinyMod.interactions(guild=GUILD) # type: ignore
async def infra_reboot(client: Client, event, hostname: ("str", "Hostname of the tinybox to reboot")):
  """Reboot a tinybox via BMC reset."""
  if event.channel.id != TINYBOX_ACCESS_CHANNEL.id: return
  if not INFRA_DIR: return
  if hostname.startswith("ci-") and not event.user.has_role(EMPLOYEE_ROLE): return

  message = yield f"Rebooting `{hostname}`..."

  p = await get_event_loop().subprocess_exec("python", "-u", SCRIPT, "--reboot", hostname, stderr=STDOUT, stdin=False)
  lines = []
  buf = b""
  while True:
    try:
      chunk = await p.stdout.read_once()
    except (EOFError, ConnectionError):
      break
    buf += chunk
    while b"\n" in buf:
      line, buf = buf.split(b"\n", 1)
      lines.append(line.decode())
      await client.interaction_response_message_edit(event, content=f"Rebooting `{hostname}`...\n```\n" + "\n".join(lines) + "\n```")
  if buf:
    lines.append(buf.decode())
  p.close()

  output = "\n".join(lines)
  rc = p.return_code or 0
  if rc != 0:
    logging.error(f"reboot_control.py --reboot {hostname} failed with rc={rc}: {output}")
    await client.interaction_response_message_edit(event, content=f"Reboot failed (exit code {rc}):\n```\n{output}\n```")
  else:
    await client.interaction_response_message_edit(event, content=f"Reboot complete for `{hostname}`.\n```\n{output}\n```")

@infra_reboot.autocomplete("hostname")
async def infra_reboot_autocomplete(event, value):
  boxes, _ = await get_box_list()
  if boxes is None: return []
  hostnames = [b["hostname"] for b in boxes]
  if not event.user.has_role(EMPLOYEE_ROLE):
    hostnames = [h for h in hostnames if not h.startswith("ci-")]
  if value: hostnames = [h for h in hostnames if value.lower() in h.lower()]
  return hostnames[:25]

@TinyMod.interactions(guild=GUILD, show_for_invoking_user_only=True) # type: ignore
async def infra_list(client: Client, event):
  """List available tinyboxes."""
  if event.channel.id != TINYBOX_ACCESS_CHANNEL.id: return
  if not INFRA_DIR: return

  boxes, err = await get_box_list()
  if boxes is None: return f"Failed to fetch box list:\n```\n{err}\n```"

  is_employee = event.user.has_role(EMPLOYEE_ROLE)
  by_method = {}
  for b in boxes:
    if not is_employee and b["hostname"].startswith("ci-"): continue
    by_method.setdefault(b["method"], []).append(b["hostname"])

  embed = Embed("Available Tinyboxes", color=0x2ecc71)
  for method, hostnames in by_method.items():
    embed.add_field(method, "\n".join(f"`{h}`" for h in hostnames), inline=True)

  return InteractionResponse(embed=embed)
