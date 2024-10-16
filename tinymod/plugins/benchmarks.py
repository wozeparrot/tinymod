from typing import Annotated
from hata import Client, Guild, ReactionAddEvent, Role, Message, Embed
from hata.ext.slash import InteractionResponse, abort
from scarletio import sleep
import pygal
from pygal.style import NeonStyle

import os, logging

from common.benchmarks import REPO, BENCHMARKS_DIR, TRACKED_BENCHMARKS, ALL_SYSTEMS, CachedBenchmarks, filter_points

TinyMod: Client
GUILD: Guild
ADMIN_ROLE: Role

GH_HEADERS = {
  "Accept": "application/vnd.github+json",
  "User-Agent": "curl/7.54.1",
  "Authorization": f"Bearer {os.environ['GH_TOKEN']}"
}
AZURE_HEADERS = {
  "Accept": "*/*",
  "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
}
CI_CHANNEL_ID = 1068993556905218128
GITHUB_WEBHOOK_ID = 1068993579520884826
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
        case "amd-train":
          artifact = [artifact["archive_download_url"] for artifact in artifacts if artifact["name"] == "Speed (AMD Training)"]
        case "mac":
          artifact = [artifact["archive_download_url"] for artifact in artifacts if artifact["name"] == "Speed (Mac)"]
        case "nvidia":
          artifact = [artifact["archive_download_url"] for artifact in artifacts if artifact["name"] == "Speed (NVIDIA)"]
        case "nvidia-train":
          artifact = [artifact["archive_download_url"] for artifact in artifacts if artifact["name"] == "Speed (NVIDIA Training)"]
        case "comma":
          artifact = [artifact["archive_download_url"] for artifact in artifacts if artifact["name"] == "Speed (comma)"]
        case _: return False

      if len(artifact) < 1: return False
      artifact = artifact[0]

      # download the artifact
      for i in range(2):
        logging.info(f"downloading artifact for run {run_number} from {artifact}")
        async with client.http.get(artifact, headers=GH_HEADERS if i == 0 else AZURE_HEADERS, redirects=0) as response:
          # save the artifact to a file
          if response.status == 200:
            # ensure that the directory for the run number exists
            (BENCHMARKS_DIR / "artifacts" / f"{run_number}").mkdir(parents=True, exist_ok=True)
            with open(BENCHMARKS_DIR / "artifacts" / f"{run_number}" / f"{system}.zip", "wb") as f:
              f.write(await response.read())
            return True
          elif response.status == 302:
            # TODO: this is kinda cursed but scarletio will remove the authorization header if the origins of the redirect don't match for security reasons
            #       but, github will redirect to a different origin for the download url, so we have to manually follow the redirect
            artifact = response.headers["Location"]
            continue
          logging.info(f"failed to download artifact for run {run_number} with response {response}")
          break
  return False

async def download_missing_benchmarks_for_system(client: Client, system: str):
  workflow_runs = REPO.get_workflow("benchmark.yml").get_runs(branch="master", status="success", event="push")
  yield workflow_runs.totalCount

  for run in workflow_runs:
    # skip all runs under 25 because they are not the right format
    if run.run_number <= 25: continue
    if not (BENCHMARKS_DIR / "artifacts" / f"{run.run_number}" / f"{system}.zip").exists():
      logging.info(f"downloading run {run.run_number} for {system}")
      succeeded = await download_benchmark(client, run.run_number, run.artifacts_url, system)
      yield run.run_number
    else: break # we can actually break here since the workflow runs are in order
    if not succeeded: break

async def auto_download_benchmarks(client: Client):
  for system in ALL_SYSTEMS:
    logging.info(f"downloading missing benchmarks for {system}")
    download = download_missing_benchmarks_for_system(client, system)
    async for run_number in download: _ = run_number

async def post_auto_download(client: Client, message: Message, embed: Embed):
  # find the run
  workflow_runs = REPO.get_workflow("benchmark.yml").get_runs(branch="master", event="push")
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

  # update the cache
  await CachedBenchmarks()._update_cache()

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
  await sleep(20 * 60) # wait 20 minutes before starting
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

@TinyMod.interactions(guild=GUILD, show_for_invoking_user_only=True) # type: ignore
async def bm_update_cache(client: Client, event,
  force: Annotated[str, ["true", "false"], "force update the cache"],
):
  """Updates the cache"""
  if not event.user.has_role(ADMIN_ROLE): return
  message = yield "updating cache..." # acknowledge the command
  await CachedBenchmarks()._update_cache(force=force == "true")
  yield InteractionResponse("done", message=message)

# ***** Benchmark utilities *****
@TinyMod.interactions(guild=GUILD, show_for_invoking_user_only=True) # type: ignore
async def bm_commit(client: Client, event,
  run_number: (int, "estimated run number to show commits around"), # type: ignore
):
  """Shows the commits around a run number"""
  message = yield "fetching commits..." # acknowledge the command

  commits = []
  workflow_runs = REPO.get_workflow("benchmark.yml").get_runs(branch="master", status="success", event="push")
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
STYLE = NeonStyle(font_family="sans-serif", title_font_size=24, legend_font_size=18, background="#151510", plot_background="#151510", foreground="#aaaaaa", foreground_strong="#f0f0f0")
def points_to_graph(title: str, legend_points: list[tuple[str, list[tuple[int, float]]]], gflops: bool = False) -> bytes:
  chart = pygal.XY(width=1280, height=800, legend_at_bottom=True, style=STYLE, title=title, x_title="Run Number", y_title="Runtime (ms)" if not gflops else "GFLOPS")
  for legend, points in legend_points: chart.add(legend, points)
  return chart.render_to_png() # type: ignore

@TinyMod.interactions(guild=GUILD) # type: ignore
async def bm_graph(client: Client, event,
  benchmark: Annotated[str, list(TRACKED_BENCHMARKS.keys()), "benchmark to graph"],
  system: ("str", "system benchmark is run on"), # type: ignore
  last_n: Annotated[int | None, RANGE, "last n runs to graph"] = None,
):
  """Graphs a benchmark"""
  if system is None or system not in ALL_SYSTEMS: abort("invalid system.")
  message = yield "graphing..." # acknowledge the command
  logging.info(f"graphing {benchmark} on {system} for last {last_n} runs")

  points = CachedBenchmarks().cache.get((benchmark, system), [])
  points = filter_points(points, last_n)

  chart = points_to_graph(f"{benchmark} on {system}", [("runtime", points)])
  yield InteractionResponse("", file=("chart.png", chart), message=message)

@bm_graph.autocomplete("system") # type: ignore
async def autocomplete_bm_graph_system(event, value):
  benchmark = event.interaction.get_value_of("benchmark")
  if benchmark is None: return

  systems = TRACKED_BENCHMARKS[benchmark][1]
  if value is None: return systems
  return [system for system in systems if value.casefold() in system]
