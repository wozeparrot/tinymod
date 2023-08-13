from typing import Annotated
from hata import Client, Guild, Role
from hata.ext.slash import InteractionResponse
from github import Github, Auth
import pygal
from pygal.style import NeonStyle

import os, csv, zipfile
from pathlib import Path

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

async def download_benchmark(client: Client, run_number: int, artifacts_url: str):
  async with client.http.get(artifacts_url, headers=GH_HEADERS) as response:
    if response.status == 200:
      artifacts = await response.json()
      artifacts = artifacts["artifacts"]

      artifact_urls = {
        "amd": [artifact["archive_download_url"] for artifact in artifacts if artifact["name"] == "Speed (AMD)"][0],
        "mac": [artifact["archive_download_url"] for artifact in artifacts if artifact["name"] == "Speed (Mac)"][0],
      }

      # download the artifacts
      for artifact in artifact_urls:
        async with client.http.get(artifact_urls[artifact], headers=GH_HEADERS) as response:
          # save the artifact to a file
          if response.status == 200:
            # ensure that the directory for the run number exists
            (BENCHMARKS_DIR / "artifacts" / f"{run_number}").mkdir(parents=True, exist_ok=True)
            with open(BENCHMARKS_DIR / "artifacts" / f"{run_number}" / f"{artifact}.zip", "wb") as f:
              f.write(await response.read())

@TinyMod.interactions(guild=GUILD, show_for_invoking_user_only=True)
async def download_benchmarks(client: Client, event):
  """Downloads the benchmark artifacts from ones that are not already downloaded"""
  if not event.user.has_role(ADMIN_ROLE): return

  # get workflow runs from github
  repo = GITHUB.get_repo("tinygrad/tinygrad")
  workflow_runs = repo.get_workflow("benchmark.yml").get_runs(branch="master", status="success", event="push")
  message = yield f"found {workflow_runs.totalCount} workflow runs"

  # get the latest workflow run
  for run in workflow_runs:
    # skip all runs under 25
    if run.run_number <= 25: continue
    yield InteractionResponse(f"downloading artifacts from run {run.run_number}", message=message)

    # fetch the artifacts from the latest workflow run
    # check if the artifacts have already been downloaded
    if not (BENCHMARKS_DIR / "artifacts" / f"{run.run_number}").exists():
      await download_benchmark(client, run.run_number, run.artifacts_url)

  yield InteractionResponse("done", message=message)

@TinyMod.interactions(guild=GUILD)
async def graph_benchmark(client: Client, event,
  system: Annotated[str, ["amd", "mac"], "system the benchmark is run on"],
  model: Annotated[str, ["resnet50", "openpilot", "efficientnet", "shufflenet"], "model the benchmark is for"],
  device: Annotated[str, ["gpu", "clang"], "device the benchmark is run on"],
  jitted: Annotated[str, ["true", "false"], "whether the benchmark is jitted or not"],
):
  """Graphs the selected benchmark"""
  points = {}

  # scan the artifacts directory for new benchmarks
  for path in (BENCHMARKS_DIR / "artifacts").glob("*"):
    # skip non-directories
    if not path.is_dir(): continue

    # open the zip file
    with zipfile.ZipFile(path / f"{system}.zip", "r") as zip:
      onnx_inference_speed_file = zip.read("onnx_inference_speed.csv").decode("utf-8")
      onnx_inference_speed_reader = csv.reader(onnx_inference_speed_file.splitlines(), delimiter=',')
      # always skip the first line
      next(onnx_inference_speed_reader)

      skip_count = 0
      if model == "openpilot": skip_count = 1
      elif model == "efficientnet": skip_count = 2
      elif model == "shufflenet": skip_count = 3
      for _ in range(skip_count): next(onnx_inference_speed_reader)

      index = 0
      if device == "gpu": index = 1
      elif device == "clang": index = 1

      if jitted == "true": index += 1

      points[int(path.name)] = float(next(onnx_inference_speed_reader)[index])

  # graph the data
  chart = pygal.XY(show_legend=False, style=NeonStyle, dots_size=4)
  chart.title = f"{system} {model} {device} {'jitted' if jitted == 'true' else 'un-jitted'}"
  chart.x_title = "run number"
  chart.y_title = "time (ms)"
  chart.add("", [(key, points[key]) for key in points])
  chart_png = chart.render_to_png()

  yield InteractionResponse(file=("chart.png", chart_png))
