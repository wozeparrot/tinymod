import math, hashlib, tempfile, os, glob
import tokenize, token, gzip, json
from datetime import datetime, timedelta
from pathlib import Path
from io import BytesIO
from typing import Optional
import pygal
from pygal.style import NeonStyle
from PIL import Image
import numpy as np
from hata import Client, Guild, Role
from hata.ext.slash import InteractionResponse
from scarletio import Lock, get_event_loop
from hata.ext import asyncio
import aiosqlite

TinyMod: Client
GUILD: Guild
ADMIN_ROLE: Role

REPO = "https://github.com/tinygrad/tinygrad.git"
BRANCH = "master"
FILE_FILTER = "tinygrad/**/*.py"
STYLE = NeonStyle(font_family="sans-serif", title_font_size=24, legend_font_size=18, background="#151510", plot_background="#151510")
WORKING_DIR = Path(tempfile.gettempdir()) / f"tinymod-{hashlib.sha256(REPO.encode()).hexdigest()}"
DATABASE = "tinymod.db"
LOOP = get_event_loop()
UPDATE_LOCK = Lock(LOOP)

METRICS_DB_COLS_NATIVE = [
  "timestamp",
  "hash",
  "gzip_size",
  "entropy",
  "linecount",
  "tokencount",
  "codelength",
  "gzip_compression_ratio",
  "tokens_per_line",
  "chars_per_line"
]
METRICS_DB_COLS_JSON = {"files_json": "files"}
async def setup(_):
  async with aiosqlite.connect(DATABASE) as db:
    await db.execute(f"CREATE TABLE IF NOT EXISTS metrics({','.join(METRICS_DB_COLS_NATIVE + list(METRICS_DB_COLS_JSON.keys()))})")
    await db.commit()

async def load_metrics():
  async with aiosqlite.connect(DATABASE) as db:
    return [{k: v for k, v in zip(METRICS_DB_COLS_NATIVE, item)} async for item in await db.execute(f"SELECT {','.join(METRICS_DB_COLS_NATIVE)} from metrics")]

async def insert_metrics(metrics: list[dict]):
  async with aiosqlite.connect(DATABASE) as db:
    await db.executemany(f"INSERT INTO metrics VALUES({','.join('?' for _ in range(len(METRICS_DB_COLS_NATIVE) + len(METRICS_DB_COLS_JSON)))})", [
      (
        *(m[col] for col in METRICS_DB_COLS_NATIVE),
        *(json.dumps(m[col]) for col in METRICS_DB_COLS_JSON.values())
      ) for m in metrics
    ])
    await db.commit()

async def get_most_recent_metric(cols: Optional[list[str]] = None):
  if cols is None: cols = METRICS_DB_COLS_NATIVE + list(METRICS_DB_COLS_JSON.keys())
  async with aiosqlite.connect(DATABASE) as db:
    cur = await db.execute(f"SELECT {','.join(cols)} from metrics WHERE timestamp = (SELECT MAX(timestamp) FROM metrics)")
    item = await cur.fetchone()
    if item: return dict((METRICS_DB_COLS_JSON[k], json.loads(v)) if k in METRICS_DB_COLS_JSON else (k, v) for k, v in zip(cols, item))
    else: return None

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
  out  = (await git_cmd("log", "--date=iso", BRANCH))[0].decode()
  cid = None
  result: list[tuple[str, float]] = []
  for l in out.splitlines():
    if l.startswith("commit "): cid = l[7:]
    if l.startswith("Date:") and cid is not None: 
      d = datetime.fromisoformat(l[5:-5].strip())
      offset = timedelta(hours=int(l[-4:-2]), minutes=int(l[-2:]))
      if l[-5] == '-': d += offset
      else: d -= offset
      result.append((cid, d.timestamp()))
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

    commits = sorted(await get_commits(), key=lambda c: c[1])
    most_recent_metric = await get_most_recent_metric(["timestamp"])
    if most_recent_metric is not None:
      commits = [c for c in commits if c[1] > most_recent_metric["timestamp"]]

    new_metrics = []
    for c in commits:
      await git_cmd("checkout", c[0])
      new_metrics.append({
        "timestamp": c[1],
        "hash": c[0],
        **get_metrics()
      })

    await insert_metrics(new_metrics)

@TinyMod.interactions(guild=GUILD) # type: ignore
async def metrics_graph(client: Client, event,
    start_offset: (int, "start offset in days from today") = None, # type: ignore
    end_offset: (int, "end offset in days from today") = None # type: ignore
):
  """Graph the line metrics"""
  message = yield "graphing..." # acknowledge the command
  await update_metrics()
  metrics = await load_metrics()

  metrics = [m for m in metrics if m["linecount"] > 0]

  if start_offset:
    min_date = (datetime.today() - timedelta(days=start_offset)).timestamp()
    metrics = [ m for m in metrics if m["timestamp"] > min_date ]

  if end_offset:
    max_date = (datetime.today() - timedelta(days=end_offset)).timestamp()
    metrics = [m for m in metrics if m["timestamp"] < max_date]

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
    chart.add("", [(datetime.fromtimestamp(m["timestamp"]), m[col]) for m in metrics])
    charts.append(Image.open(BytesIO(chart.render_to_png()))) # type: ignore

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
async def metric_table(client: Client, event,):
  """Show the line metrics table"""
  message = yield "generating the table..." # acknowledge the command

  await update_metrics()
  metric = await get_most_recent_metric()

  label_key_map = {
    "Lines": "linecount",
    "Tokens/Line": "tokens_per_line",
  }

  table_cells = []
  table_cells.append(["file in `tinygrad/`"] + list(label_key_map.keys()))
  table_cells.append(["---" for _ in range(len(label_key_map.keys()) + 1)])
  for fm in sorted(metric["files"], key=lambda fm: fm["filename"]): # type: ignore
    table_cells.append([fm["filename"].replace("tinygrad/", "")] + ["{:.1f}".format(fm[label_key_map[label]]) for label in label_key_map.keys()])
  table_cells.append(["---" for _ in range(len(label_key_map.keys()) + 1)])
  table_cells.append(["total"] + ["{:.1f}".format(metric[label_key_map[label]]) for label in label_key_map.keys()]) # type: ignore

  col_widths = [max(len(row[i]) for row in table_cells) for i in range(len(table_cells[0]) - 1)] + [0]
  txt_table = "\n".join(" | ".join(cell.ljust(col_widths[i]) for i, cell in enumerate(row)) for row in table_cells)

  if len(txt_table) < 1992:
    yield InteractionResponse(f"```\n{txt_table}\n```", message=message)
  else:
    yield InteractionResponse("", file=("metrics.txt", txt_table), message=message)
