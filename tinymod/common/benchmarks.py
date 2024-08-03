from github import Github, Auth

import zipfile, re, os, logging, time
from pathlib import Path
from math import inf

GITHUB = Github(auth=Auth.Token(os.environ["GH_TOKEN"]))
REPO = GITHUB.get_repo("tinygrad/tinygrad")

BENCHMARKS_DIR = Path("persist/benchmarks")
def get_benchmarks(filename: str, system: str, start: int = 0):
  for path in (BENCHMARKS_DIR / "artifacts").iterdir():
    if (run_number := int(path.name)) <= start: continue
    if not path.is_dir(): continue
    if not (path / f"{system}.zip").exists(): continue
    with zipfile.ZipFile(path / f"{system}.zip") as zip:
      if filename not in zip.namelist(): continue
      with zip.open(filename) as f:
        yield run_number, f.read().decode()

REGEXES = {
  "sd": re.compile(r"step in (\d+\.\d+) ms"),
  "llama": re.compile(r"total[ ]+(\d+\.\d+) ms"),
  "mixtral": re.compile(r"total[ ]+(\d+\.\d+) ms"),
  "gpt2": re.compile(r"ran model in[ ]+(\d+\.\d+) ms"),
  "cifar": re.compile(r"\d+[ ]+(\d+\.\d+) ms run,"),
  "resnet": re.compile(r"\d+[ ]+(\d+\.\d+) ms run,"),
  "openpilot_compile": re.compile(r"s/[ ]+(\d+\.\d+)ms"),
  "openpilot": re.compile(r"jitted:[ ]+(\d+\.\d+) ms"),
}

ALL_SYSTEMS = ["amd", "amd-train", "nvidia", "nvidia-train", "mac", "comma"]

# regex, systems, skip_count, max_count
TRACKED_BENCHMARKS = {
  # stable diffusion
  "sd.txt": (REGEXES["sd"], ["amd", "mac", "nvidia"], 3, 0),
  "sdxl.txt": (REGEXES["sd"], ["amd", "mac", "nvidia"], 3, 0),
  # llama
  "llama_unjitted.txt": (REGEXES["llama"], ["amd", "mac", "nvidia"], 4, 0),
  "llama_jitted.txt": (REGEXES["llama"], ["amd", "mac", "nvidia"], 4, 0),
  "llama_beam.txt": (REGEXES["llama"], ["amd", "mac", "nvidia"], 4, 0),
  "llama_2_70B.txt": (REGEXES["llama"], ["amd", "nvidia"], 4, 0),
  "llama_four_gpu.txt": (REGEXES["llama"], ["amd", "nvidia"], 4, 0),
  "llama_six_gpu.txt": (REGEXES["llama"], ["amd", "nvidia"], 4, 0),
  # llama3
  "llama3_beam.txt": (REGEXES["llama"], ["amd", "nvidia"], 4, 0),
  "llama3_four_gpu.txt": (REGEXES["llama"], ["amd", "nvidia"], 4, 0),
  "llama3_six_gpu.txt": (REGEXES["llama"], ["amd", "nvidia"], 4, 0),
  # mixtral
  "mixtral.txt": (REGEXES["mixtral"], ["amd"], 3, 0),
  # gpt2
  "gpt2_unjitted.txt": (REGEXES["gpt2"], ["amd", "mac", "nvidia"], 4, 0),
  "gpt2_jitted.txt": (REGEXES["gpt2"], ["amd", "mac", "nvidia"], 4, 0),
  "gpt2_half.txt": (REGEXES["gpt2"], ["amd", "mac", "nvidia"], 4, 0),
  "gpt2_half_beam.txt": (REGEXES["gpt2"], ["amd", "mac", "nvidia"], 4, 0),
  # cifar
  "train_cifar.txt": (REGEXES["cifar"], ["amd-train", "mac", "nvidia-train"], 3, 0),
  "train_cifar_half.txt": (REGEXES["cifar"], ["amd-train", "mac", "nvidia-train"], 3, 0),
  "train_cifar_bf16.txt": (REGEXES["cifar"], ["amd-train", "nvidia-train"], 3, 0),
  "train_cifar_one_gpu.txt": (REGEXES["cifar"], ["amd-train", "nvidia-train"], 3, 20),
  "train_cifar_six_gpu.txt": (REGEXES["cifar"], ["amd-train", "nvidia-train"], 3, 20),
  # resnet
  "train_resnet_one_gpu.txt": (REGEXES["resnet"], ["amd-train", "nvidia-train"], 3, 0),
  "train_resnet.txt": (REGEXES["resnet"], ["amd-train", "nvidia-train"], 3, 0),
  # openpilot
  "openpilot_compile_0_9_4.txt": (REGEXES["openpilot_compile"], ["comma"], 0, -1),
  "openpilot_compile_0_9_7.txt": (REGEXES["openpilot_compile"], ["comma"], 0, -1),
  "openpilot_0_9_4.txt": (REGEXES["openpilot"], ["comma"], 8, 0),
  "openpilot_0_9_7.txt": (REGEXES["openpilot"], ["comma"], 8, 0),
  "openpilot_image_0_9_4.txt": (REGEXES["openpilot"], ["comma"], 8, 0),
  "openpilot_image_0_9_7.txt": (REGEXES["openpilot"], ["comma"], 8, 0),
}

def regex_extract_benchmark(regex: re.Pattern, benchmark: str, skip_count: int, max_count: int = 0) -> float:
  iter = regex.finditer(benchmark)
  try:
    for _ in range(skip_count): next(iter)
  except: return -inf
  sums, counts = 0, 0
  for match in iter:
    sums += float(match.group(1))
    counts += 1
    if max_count > 0 and counts >= max_count: break
  if counts == 0: return -inf
  if max_count == -1: return round(float(match.group(1)), 2)
  return round(sums / counts, 2)

def regex_benchmark_to_points(regex: re.Pattern, filename: str, system: str, skip_count: int, max_count: int = 0, start: int = 0) -> list[tuple[int, float]]:
  points = []
  for run_number, benchmark in get_benchmarks(filename, system, start):
    runtime = regex_extract_benchmark(regex, benchmark, skip_count, max_count)
    points.append((run_number, runtime))
  return points

# def filter_outliers_by_var(points: list[tuple[int, float]], stddev_multiplier: float = 2) -> list[tuple[int, float]]:
#   points = sorted(points, key=lambda x: x[1])
#   avg = sum(point[1] for point in points) / len(points)
#   std = (sum((point[1] - avg) ** 2 for point in points) / len(points))
#   return [point for point in points if abs(point[1] - avg) < stddev_multiplier * std]

def filter_points_slower_than_latest(points: list[tuple[int, float]], multiplier: float = 5) -> list[tuple[int, float]]:
  if len(points) == 0: return points
  points = sorted(points, key=lambda x: x[0])
  latest = points[-1][1]
  return [point for point in points if point[1] < latest * multiplier]

def filter_points(points: list[tuple[int, float]], last_n: int | None) -> list[tuple[int, float]]:
  points = [point for point in points if point[1] != -inf]
  # points = sorted(points, key=lambda x: x[0])
  # if len(points) > 10:
  #   points = filter_outliers_by_var(points[:-5]) + points[-5:]
  points = filter_points_slower_than_latest(points)
  points = sorted(points, key=lambda x: x[0])
  if last_n is not None: points = points[-last_n:]
  return points

class _CachedBenchmarks:
  def __init__(self):
    self.last_run = 0
    self.cache, self.commit_cache, self.curr_commit = {}, {}, ""
    self._update_cache()

  def _update_cache(self, force:bool=False):
    logging.info("Updating cached benchmarks.")
    if not force and (BENCHMARKS_DIR / "artifacts").stat().st_mtime <= self.last_run: return

    # update cache
    for file, (regex, systems, skip_count, max_count) in TRACKED_BENCHMARKS.items():
      for system in systems:
        points = regex_benchmark_to_points(regex, file, system, skip_count, max_count)
        points = filter_points(points, None)
        self.cache[(file, system)] = points

    # tie recent 300 benchmark run numbers to a commit
    workflow_runs = REPO.get_workflow("benchmark.yml").get_runs(branch="master", status="success", event="push")
    latest_run = int(max((BENCHMARKS_DIR / "artifacts").iterdir(), key=lambda x: int(x.name)).name)
    for run in workflow_runs:
      if run.run_number not in self.commit_cache and run.run_number <= latest_run:
        self.commit_cache[run.run_number] = run.head_sha
      if run.run_number == latest_run: self.curr_commit = run.head_sha

    self.last_run = time.time()
    logging.info(f"Cached benchmarks updated. Current commit: {self.curr_commit}")
CachedBenchmarks = _CachedBenchmarks()
