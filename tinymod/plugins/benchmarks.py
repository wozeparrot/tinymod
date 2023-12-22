from typing import Annotated
from hata import Client, Guild, ReactionAddEvent, Role, Message, Embed
from hata.ext.slash import InteractionResponse
from scarletio import sleep
from github import Github, Auth
import pygal
from pygal.style import NeonStyle

import os, zipfile, re
from pathlib import Path
from math import inf

TinyMod: Client
GUILD: Guild
ADMIN_ROLE: Role

GITHUB = Github(auth=Auth.Token(os.environ["GH_TOKEN"]))
BENCHMARKS_DIR = Path("benchmarks")
GH_HEADERS = {
  "Accept": "application/vnd.github+json",
  "User-Agent": "curl/7.54.1",
  "Authorization": f"Bearer {os.environ['GH_TOKEN']}"
}
CI_CHANNEL_ID = 1068993556905218128
GITHUB_WEBHOOK_ID = 1068993579520884826
ALL_SYSTEMS = ["amd", "mac", "nvidia"]
RANGE = range(10, 100 + 1, 10)

# ***** Downloading benchmarks *****
async def download_benchmark(client: Client, run_number: int, artifacts_url: str, system: str) -> bool:
  async with client.http.get(artifacts_url, headers=GH_HEADERS) as response:
    if response.status == 200:
      artifacts = await response.json()
      artifacts = artifacts["artifacts"]

      match (system):
        case "amd":
            artifact = [artifact["archive_download_url"] for artifact in artifacts if artifact["name"] == "Speed (AMD)"]
        case "mac":
            artifact = [artifact["archive_download_url"] for artifact in artifacts if artifact["name"] == "Speed (Mac)"]
        case "nvidia":
            artifact = [artifact["archive_download_url"] for artifact in artifacts if artifact["name"] == "Speed (NVIDIA)"]
        case _: return False

      if len(artifact) < 1: return False
      artifact = artifact[0]

      # download the artifact
      async with client.http.get(artifact, headers=GH_HEADERS) as response:
        # save the artifact to a file
        if response.status == 200:
          # ensure that the directory for the run number exists
          (BENCHMARKS_DIR / "artifacts" / f"{run_number}").mkdir(parents=True, exist_ok=True)
          with open(BENCHMARKS_DIR / "artifacts" / f"{run_number}" / f"{system}.zip", "wb") as f:
            f.write(await response.read())
          return True
        else:
          print(f"failed to download artifact for run {run_number} with response {response}")
  return False

async def download_missing_benchmarks_for_system(client: Client, system: str):
  repo = GITHUB.get_repo("tinygrad/tinygrad")
  workflow_runs = repo.get_workflow("benchmark.yml").get_runs(branch="master", status="success", event="push")
  yield workflow_runs.totalCount

  for run in workflow_runs:
    # skip all runs under 25 because they are not the right format
    if run.run_number <= 25: continue
    if not (BENCHMARKS_DIR / "artifacts" / f"{run.run_number}" / f"{system}.zip").exists():
      print(f"downloading run {run.run_number} for {system}")
      succeeded = await download_benchmark(client, run.run_number, run.artifacts_url, system)
      yield run.run_number
    else: break # we can actually break here since the workflow runs are in order
    if not succeeded: break

async def auto_download_benchmarks(client: Client):
  for system in ALL_SYSTEMS:
    print(f"downloading missing benchmarks for {system}")
    download = download_missing_benchmarks_for_system(client, system)
    async for run_number in download: _ = run_number

async def post_auto_download(client: Client, message: Message, embed: Embed):
  # find the run
  repo = GITHUB.get_repo("tinygrad/tinygrad")
  workflow_runs = repo.get_workflow("benchmark.yml").get_runs(branch="master", event="push")
  for run in workflow_runs:
    if run.head_sha == embed.url.split("/")[-1]:
      break
  else:
    await client.reaction_add(message, "❓")
    return

  # check run status and conclusion
  if run.status != "completed" or run.conclusion != "success":
    await client.reaction_add(message, "❌")
    return

  # check if the run is downloaded
  if not (BENCHMARKS_DIR / "artifacts" / f"{run.run_number}").exists():
    await client.reaction_add(message, "⛔")
    return

  # its good
  await client.reaction_add(message, "✅")

  # TODO: fire off the regression check

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

  # queue the download
  await client.reaction_add(message, "⬇️")
  await sleep(10 * 60) # wait 10 minutes before starting
  await auto_download_benchmarks(client)
  await client.reaction_clear(message)

  await post_auto_download(client, message, embed)

@TinyMod.events # type: ignore
async def reaction_add(client: Client, event: ReactionAddEvent):
  message = event.message
  if message.channel.id != CI_CHANNEL_ID: return
  if event.user.bot: return
  if not event.user.has_role(ADMIN_ROLE): return
  message = await client.message_get(message)
  if message.author.id != GITHUB_WEBHOOK_ID: return

  # check if it is a commit to master
  if message.embeds is None: return
  if len(message.embeds) < 1: return
  embed = message.embeds[0]
  if "[tinygrad:master]" not in embed.title: return
  if "new commit" not in embed.title: return

  # requeue the download
  await client.reaction_clear(message)
  await client.reaction_add(message, "⬇️")
  await auto_download_benchmarks(client)
  await client.reaction_clear(message)

  await post_auto_download(client, message, embed)

@TinyMod.interactions(guild=GUILD, show_for_invoking_user_only=True) # type: ignore
async def bm_download_missing(client: Client, event,
  system: Annotated[str, ALL_SYSTEMS, "system to download missing benchmarks for"]
):
  """Downloads the missing benchmarks for a system"""
  if not event.user.has_role(ADMIN_ROLE): return
  download = download_missing_benchmarks_for_system(client, system)
  message = yield f"found {await anext(download)} runs"
  async for run_number in download:
    yield InteractionResponse(f"downloaded run {run_number}", message=message)
  yield InteractionResponse("done", message=message)

@TinyMod.interactions(guild=GUILD, show_for_invoking_user_only=True) # type: ignore
async def bm_download_missing_for_all(client: Client, event):
  """Downloads the missing benchmarks for all systems"""
  if not event.user.has_role(ADMIN_ROLE): return
  message = yield "downloading..."
  for system in ALL_SYSTEMS:
    download = download_missing_benchmarks_for_system(client, system)
    yield InteractionResponse(f"found {await anext(download)} runs for {system}", message=message)
    async for run_number in download:
      yield InteractionResponse(f"downloaded run {run_number} - {system}", message=message)
  yield InteractionResponse("done", message=message)

# ***** Benchmark utilities *****
@TinyMod.interactions(guild=GUILD, show_for_invoking_user_only=True) # type: ignore
async def bm_commit(client: Client, event,
  run_number: (int, "estimated run number to show commits around"), # type: ignore
):
  """Shows the commits around a run number"""
  message = yield "fetching commits..." # acknowledge the command

  commits = []
  repo = GITHUB.get_repo("tinygrad/tinygrad")
  workflow_runs = repo.get_workflow("benchmark.yml").get_runs(branch="master", status="success", event="push")
  for run in workflow_runs:
    if run.run_number in range(run_number - 5, run_number + 5):
      try: commits.append({"run": run.run_number, "sha": run.head_sha, "message": run.head_commit.message.split("\n")[0], "link": run.html_url})
      except: continue
    if run.run_number <= run_number - 5: break

  # build message
  send_message = f"Commits around run {run_number}:\n"
  for commit in commits:
    send_message += f"[`{commit['sha'][:7]}`](<{commit['link']}>) - {commit['message']}"
    if commit["run"] == run_number: send_message += f" **<-- run {run_number}**\n"
    else: send_message += "\n"

  yield InteractionResponse(send_message, message=message)

# ***** Graphing benchmarks *****
def get_benchmarks(filename: str, system: str):
  for path in (BENCHMARKS_DIR / "artifacts").iterdir():
    if not path.is_dir(): continue
    if not (path / f"{system}.zip").exists(): continue
    with zipfile.ZipFile(path / f"{system}.zip") as zip:
      if filename not in zip.namelist(): continue
      with zip.open(filename) as f:
        yield int(path.name), f.read().decode()

def regex_extract_benchmark(regex: re.Pattern, benchmark: str, skip_count: int) -> float:
  iter = regex.finditer(benchmark)
  try:
    for _ in range(skip_count): next(iter)
  except: return -inf
  sums, counts = 0, 0
  for match in iter:
    sums += float(match.group(1))
    counts += 1
  if counts == 0: return -inf
  return round(sums / counts, 2)

def filter_outliers_by_stddev(points: list[tuple[int, float]], stddev_multiplier: float = 2) -> list[tuple[int, float]]:
  points = sorted(points, key=lambda x: x[1])
  avg = sum(point[1] for point in points) / len(points)
  std = (sum((point[1] - avg) ** 2 for point in points) / len(points)) ** 0.5
  return [point for point in points if abs(point[1] - avg) < stddev_multiplier * std]

STYLE = NeonStyle(font_family="sans-serif", title_font_size=24, legend_font_size=18, background="#151510", plot_background="#151510")
def points_to_graph(title: str, legend_points: list[tuple[str, list[tuple[int, float]]]], last_n: int | None, gflops: bool = False) -> bytes:
  chart = pygal.XY(width=1280, height=800, legend_at_bottom=True, style=STYLE, title=title, x_title="Run Number", y_title="Runtime (ms)" if not gflops else "GFLOPS")
  for legend, points in legend_points:
    points = filter_outliers_by_stddev(points) if len(points) > 10 else points
    points = sorted(points, key=lambda x: x[0])
    if last_n is not None:
        points = points[-last_n:]
    chart.add(legend, points)
  return chart.render_to_png()

BM_GRAPH = TinyMod.interactions(None, name="bm-graph", description="Graphs a benchmark", guild=GUILD) # type: ignore

SD_REGEX = re.compile(r"step in (\d+\.\d+) ms")
@BM_GRAPH.interactions
async def stable_diffusion(client: Client, event,
  system: Annotated[str, ["amd", "mac"], "system to graph"],
  last_n: Annotated[int | None, RANGE, "last n runs to graph"] = None,
):
  """Graphs the stable diffusion benchmark"""
  message = yield "graphing..." # acknowledge the command

  points = []
  for run_number, benchmark in get_benchmarks("sd.txt", system):
    runtime = regex_extract_benchmark(SD_REGEX, benchmark, 3)
    if runtime == -inf: continue
    points.append((run_number, runtime))

  chart = points_to_graph(f"{system} Stable Diffusion", [("runtime", points)], last_n)
  yield InteractionResponse("", file=("chart.png", chart), message=message)

LLAMA_REGEX = re.compile(r"total (\d+\.\d+) ms")
@BM_GRAPH.interactions
async def llama(client: Client, event,
  system: Annotated[str, ["amd", "mac"], "system to graph"],
  jit: Annotated[str | bool, ["true", "false"], "jitted?"],
  last_n: Annotated[int | None, RANGE, "last n runs to graph"] = None,
):
  """Graphs the llama benchmark"""
  message = yield "graphing..." # acknowledge the command
  jit = jit == "true"

  points = []
  for run_number, benchmark in get_benchmarks("llama_jitted.txt" if jit else "llama_unjitted.txt", system):
    runtime = regex_extract_benchmark(LLAMA_REGEX, benchmark, 3)
    if runtime == -inf: continue
    points.append((run_number, runtime))

  chart = points_to_graph(f"{system} Llama{' jitted' if jit else ''}", [("runtime", points)], last_n)
  yield InteractionResponse("", file=("chart.png", chart), message=message)

GPT2_REGEX = re.compile(r"total (\d+\.\d+) ms")
@BM_GRAPH.interactions
async def gpt2(client: Client, event,
  system: Annotated[str, ALL_SYSTEMS, "system to graph"],
  jit: Annotated[str | bool, ["true", "false"], "jitted?"],
  last_n: Annotated[int | None, RANGE, "last n runs to graph"] = None,
):
  """Graphs the gpt2 benchmark"""
  message = yield "graphing..." # acknowledge the command
  jit = jit == "true"

  points = []
  for run_number, benchmark in get_benchmarks("gpt2_jitted.txt" if jit else "gpt2_unjitted.txt", system):
    runtime = regex_extract_benchmark(LLAMA_REGEX, benchmark, 3)
    if runtime == -inf: continue
    points.append((run_number, runtime))

  chart = points_to_graph(f"{system} GPT2{' jitted' if jit else ''}", [("runtime", points)], last_n)
  yield InteractionResponse("", file=("chart.png", chart), message=message)

@BM_GRAPH.interactions
async def gpt2_beam(client: Client, event):
  """Graphs the gpt2 benchmark on nvidia with beam and half"""
  message = yield "graphing..." # acknowledge the command

  points = []
  for run_number, benchmark in get_benchmarks("gpt2_half_beam.txt", "nvidia"):
    runtime = regex_extract_benchmark(GPT2_REGEX, benchmark, 3)
    if runtime == -inf: continue
    points.append((run_number, runtime))

  chart = points_to_graph(f"nvidia GPT2 beam + half", [("runtime", points)], None)
  yield InteractionResponse("", file=("chart.png", chart), message=message)


# ***** Regression testing *****
async def check_regression(client: Client, run_number: int, system: str):
  pass
