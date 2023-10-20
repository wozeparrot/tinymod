import math
import shelve
import hashlib
import tempfile
import os
from datetime import datetime, timedelta
from pathlib import Path
import tokenize
import token
import gzip
from io import BytesIO
import pygal
from pygal.style import NeonStyle
from PIL import Image
import glob
import numpy as np
from hata import Client, Guild, Role
from hata.ext.slash import InteractionResponse
from scarletio import Lock, get_event_loop

TinyMod: Client
GUILD: Guild
ADMIN_ROLE: Role

REPO = "https://github.com/tinygrad/tinygrad.git"
BRANCH = "master"
FILE_FILTER = "tinygrad/**/*.py"
STYLE = NeonStyle(font_family="sans-serif", title_font_size=24, legend_font_size=18, background="#151510", plot_background="#151510")

WORKING_DIR = Path(tempfile.gettempdir()) / f"tinymod-{hashlib.sha256(REPO.encode()).hexdigest()}"
CACHE = shelve.open("metrics.cache")
LOOP = get_event_loop()
UPDATE_LOCK = Lock(LOOP)

async def git_cmd(*args):
  p = await LOOP.subprocess_shell(" ".join(["git", *args]), cwd=WORKING_DIR)
  return await p.communicate()

async def clone_or_pull():
  if not os.path.exists(WORKING_DIR): os.mkdir(WORKING_DIR)
  if not os.path.exists(os.path.join(WORKING_DIR, ".git")):
    await git_cmd("clone", REPO, ".")
    await git_cmd("checkout", BRANCH)
  else: 
    await git_cmd("checkout", BRANCH)
    await git_cmd("pull")

async def get_commits():
  out, _ = await git_cmd("log", "--reflog", "--date=iso")
  out = out.decode("utf-8")
  cid = None
  result: list[tuple[str, datetime]] = []
  for l in out.splitlines():
    if l.startswith("commit "): cid = l[7:]
    if l.startswith("Date:") and cid is not None: 
      d = datetime.fromisoformat(l[5:-5].strip())
      offset = timedelta(hours=int(l[-4:-2]), minutes=int(l[-2:]))
      if l[-5] == '-': d += offset
      else: d -= offset
      result.append((cid, d))
  return result

def entropy(code: str, base=2):
  counts = np.array([code.count(c) for c in set(code)])
  norm_counts = counts / counts.sum()
  return -(norm_counts * np.log(norm_counts) / np.log(base)).sum()

def append_computed_metrics(m: dict):
  return {
    **m,
    "gzip_compression_ratio": m["codelength"] / m["gzip_size"] if "gzip_size" in m else 0,
    "tokens_per_line": 0 if m["linecount"] == 0 else m["tokencount"] / m["linecount"],
    "chars_per_line": 0 if m["linecount"] == 0 else m["codelength"] / m["linecount"]
  }

def get_metrics():
  TOKEN_WHITELIST = [token.OP, token.NAME, token.NUMBER, token.STRING]
  all_code: list[bytes] = []
  file_metrics = []

  for fn in glob.iglob(os.path.join(WORKING_DIR, FILE_FILTER), recursive=True):
    with open(fn, "rb") as fd:
      code = fd.read()
      io = BytesIO(code)
      tokens = [t for t in tokenize.tokenize(io.readline) if t.type in TOKEN_WHITELIST]
      file_metrics.append(append_computed_metrics({
        "linecount": len(set([t.start[0] for t in tokens])),
        "tokencount": len(tokens),
        "codelength": len(code),
        "filename": os.path.relpath(fn, WORKING_DIR)
      }))
      all_code.append(code)

  code = b''.join(all_code)

  sum_keys = ["linecount", "tokencount", "codelength"]

  return append_computed_metrics({
    "files": file_metrics,
    "gzip_size": len(gzip.compress(code)),
    "entropy": entropy(code.decode("utf-8")),
    **{k: sum(m[k] for m in file_metrics) for k in sum_keys}
  })

async def update_metrics():
  async with UPDATE_LOCK:
    await clone_or_pull()
    old_metrics = CACHE[BRANCH] if BRANCH in CACHE else []

    commits = sorted(await get_commits(), key=lambda c: c[1])
    if len(old_metrics) > 0:
      last_date: datetime = max(m["date"] for m in old_metrics)
      commits = [c for c in commits if c[1] > last_date]

    new_metrics = []
    for c in commits:
      await git_cmd("checkout", c[0])
      new_metrics.append({
        "date": c[1],
        "hash": c[0],
        **get_metrics()
      }) 

    CACHE[BRANCH] = list({ m["date"].date(): m for m in old_metrics + new_metrics }.values())

@TinyMod.interactions(guild=GUILD) # type: ignore
async def metric_graph(
    start_offset: (int, "start offset in days from today") = None, # type: ignore
    end_offset: (int, "end offset in days from today") = None # type: ignore
):
  """Graph the line metrics"""
  message = yield "graphing..." # acknowledge the command
  await update_metrics()
  metrics = CACHE[BRANCH]

  metrics = [m for m in metrics if m["linecount"] > 0]

  if start_offset:
    min_date = datetime.today() - timedelta(days=start_offset)
    metrics = [m for m in metrics if m["date"] > min_date]

  if end_offset:
    max_date = datetime.today() - timedelta(days=end_offset)
    metrics = [m for m in metrics if m["date"] < max_date]

  charts = []
  for col, title in [
        ("linecount", "line count"),
        ("tokens_per_line", "tokens/line"),
        ("tokencount", "token count"),
        ("entropy", "bits/char (entropy)"),
        ("chars_per_line", "chars/line"),
        ("gzip_compression_ratio", "gzip compression ratio"),
      ]:
    chart = pygal.DateTimeLine(
      width=800, height=500,
      style=STYLE,
      show_legend=False,
      show_dots=False,
      x_label_rotation=35, truncate_label=-1,
      x_value_formatter=lambda dt: dt.strftime('%d, %b %Y')
    )

    chart.title = title
    chart.add("", [(m["date"], m[col]) for m in metrics])
    charts.append(Image.open(BytesIO(chart.render_to_png())))

  chart_size = (max(c.width for c in charts), max(c.height for c in charts))
  w = int(len(charts) ** 0.5)
  h = math.ceil(len(charts) / w)
  full_chart = Image.new("RGB", size=(w * chart_size[0], h * chart_size[1]))
  for idx, c in enumerate(charts):
    full_chart.paste(c, ((idx % w) * chart_size[0], int(idx / w) * chart_size[1]))

  chart_raw = BytesIO()
  full_chart.save(chart_raw, format="PNG")
  yield InteractionResponse("", file=("chart.png", chart_raw.getvalue()), message=message)
  
@TinyMod.interactions(guild=GUILD) # type: ignore
async def metric_table(client: Client, event,
  commit: (str, "commit to create the table for") = None # type: ignore
):
  """Show the line metrics table"""
  message = yield "generating the table..." # acknowledge the command
  await update_metrics()
  metrics = CACHE[BRANCH]

  if commit is None:
    metric = max(metrics, key=lambda m: m["date"])
  else:
    metric = next((m for m in metrics if m["hash"] == commit), None)
    if metric is None:
      await client.interaction_response_message_create(event, f"commit with hash {commit} not found", show_for_invoking_user_only=True)
      return

  label_key_map = {
    "Lines": "linecount",
    "Tokens": "tokencount",
    "Tokens/Line": "tokens_per_line",
    "Chars/Line": "chars_per_line"
  }

  md_table = []
  md_table.append(" | file | " + " | ".join(label_key_map.keys()))
  md_table.append(" | " + " | ".join([ "---" for _ in range(len(label_key_map.keys()) + 1)]))
  for fm in sorted(metric["files"], key=lambda fm: fm["filename"]):
    md_table.append(" | " + " | ".join([ fm["filename"] ] + [ "{:.1f}".format(fm[label_key_map[label]]) for label in label_key_map.keys()]))
  md_table.append(" | " + " | ".join([ "---" for _ in range(len(label_key_map.keys()) + 1)]))
  md_table.append(" | **total** | " + " | ".join([ "**{:.1f}**".format(metric[label_key_map[label]]) for label in label_key_map.keys()]))

  yield InteractionResponse("\n".join(md_table), message=message)
