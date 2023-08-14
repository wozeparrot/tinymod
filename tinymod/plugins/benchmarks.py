from typing import Annotated
from hata import Client, Guild, Role
from hata.ext.slash import InteractionResponse
from github import Github, Auth
import pygal
from pygal.style import NeonStyle

import os, csv, zipfile, re
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

LLAMA_REGEX = re.compile(r"ran model in (\d+\.\d+) ms")
LLAMA_REGEX_2 = re.compile(r"sync in (\d+\.\d+) ms")
CIFAR_REGEX = re.compile(r"(\d+\.\d+) ms run")
CIFAR_REGEX_2 = re.compile(r"(\d+\.\d+) ms CL")

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
    else: # we can actually break here since the workflow runs are in order
      break

  yield InteractionResponse("done", message=message)

@TinyMod.interactions(guild=GUILD)
async def graph_benchmark(client: Client, event,
  system: Annotated[str, ["amd", "mac"], "system the benchmark is run on"],
  model: Annotated[str, ["resnet50", "openpilot", "efficientnet", "shufflenet", "llama", "cifar"], "model the benchmark is for"],
  device: Annotated[str, ["clang", "gpu"], "device the benchmark is run on"],
  jitted: Annotated[str, ["true", "false"], "whether the benchmark is jitted or not"],
  sync: Annotated[str, ["true", "false"], "show the sync time or not"]
):
  """Graphs the selected benchmark"""
  points, points_2, good_to_graph = [], [], True
  legend, legend_2 = "", ""

  if model == "llama":
    if device != "gpu":
      yield "llama only runs on gpu"
      good_to_graph = False
    else:
      for path in (BENCHMARKS_DIR / "artifacts").glob("*"):
        # skip non-directories
        if not path.is_dir(): continue

        # open the zip file
        with zipfile.ZipFile(path / f"{system}.zip", "r") as zip:
          # some of the older artifacts don't have llama so we just skip
          if f"llama_{'jitted' if jitted == 'true' else 'unjitted'}.txt" not in zip.namelist(): continue
          llama_file = zip.read(f"llama_{'jitted' if jitted == 'true' else 'unjitted'}.txt").decode("utf-8")
          # the runtime is part of the string "ran model in {runtime} ms" so we use regex to extract it
          runtime_strs_found = LLAMA_REGEX.finditer(llama_file)
          for _ in range(3): next(runtime_strs_found) # skip first 3 runs for warmup
          # average the rest of the runs
          runtime_sum, runtime_len = 0, 0
          for runtime_str in runtime_strs_found:
            runtime_sum += float(runtime_str.group(1))
            runtime_len += 1
          points.append((int(path.name), runtime_sum / runtime_len))
          # do the same for the second regex
          if sync == "true":
            sync_strs_found = LLAMA_REGEX_2.finditer(llama_file)
            for _ in range(3): next(sync_strs_found) # skip first 3 runs for warmup
            # average the rest of the runs
            sync_sum, sync_len = 0, 0
            for sync_str in sync_strs_found:
              sync_sum += float(sync_str.group(1))
              sync_len += 1
            points_2.append((int(path.name), sync_sum / sync_len))
      legend, legend_2 = "runtime", "sync time"
  elif model == "cifar":
    if device != "gpu" or jitted != "true":
      yield "cifar only runs on gpu and jitted"
      good_to_graph = False
    else:
      for path in (BENCHMARKS_DIR / "artifacts").glob("*"):
        # skip non-directories
        if not path.is_dir(): continue

        # open the zip file
        with zipfile.ZipFile(path / f"{system}.zip", "r") as zip:
          # some of the older artifacts don't have cifar so we just skip
          if "train_cifar.txt" not in zip.namelist(): continue
          cifar_file = zip.read("train_cifar.txt").decode("utf-8")
          # extract the runtime
          runtime_strs_found = CIFAR_REGEX.finditer(cifar_file)
          for _ in range(3): next(runtime_strs_found) # skip first 3 runs for warmup
          # average the rest of the runs
          runtime_sum, runtime_len = 0, 0
          for runtime_str in runtime_strs_found:
            runtime_sum += float(runtime_str.group(1))
            runtime_len += 1
          points.append((int(path.name), runtime_sum / runtime_len))
          # do the same for the second regex
          if sync == "true":
            sync_strs_found = CIFAR_REGEX_2.finditer(cifar_file)
            for _ in range(3): next(sync_strs_found)
            # average the rest of the runs
            sync_sum, sync_len = 0, 0
            for sync_str in sync_strs_found:
              sync_sum += float(sync_str.group(1))
              sync_len += 1
            points_2.append((int(path.name), sync_sum / sync_len))
      legend, legend_2 = "runtime", "CL time"
  else: # onnx model
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

        points.append((int(path.name), float(next(onnx_inference_speed_reader)[index])))
    legend = "runtime"

  if good_to_graph:
    # graph the data
    chart = pygal.XY(legend_at_bottom=True, style=NeonStyle, dots_size=4)
    chart.title = f"{system} {model} {device} {'jitted' if jitted == 'true' else 'un-jitted'}"
    chart.x_title = "run number"
    chart.y_title = "time (ms)"
    chart.add(legend, sorted(points, key=lambda x: x[0]))
    if len(points_2) > 0:
      chart.add(legend_2, sorted(points_2, key=lambda x: x[0]))
    chart_png = chart.render_to_png()

    yield InteractionResponse(file=("chart.png", chart_png))