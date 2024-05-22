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
}

ALL_SYSTEMS = ["amd", "amd-train", "nvidia", "nvidia-train", "mac"]

# regex, systems, skip_count, max_count
TRACKED_BENCHMARKS = {
  # stable diffusion
  "sd.txt": (REGEXES["sd"], ["amd", "mac", "nvidia"], 3, 0),
  # llama
  "llama_unjitted.txt": (REGEXES["llama"], ["amd", "mac", "nvidia"], 4, 0),
  "llama_jitted.txt": (REGEXES["llama"], ["amd", "mac", "nvidia"], 4, 0),
  "llama_beam.txt": (REGEXES["llama"], ["amd", "mac", "nvidia"], 4, 0),
  "llama_2_70B.txt": (REGEXES["llama"], ["amd", "nvidia"], 4, 0),
  "llama_four_gpu.txt": (REGEXES["llama"], ["amd", "nvidia"], 4, 0),
  "llama_six_gpu.txt": (REGEXES["llama"], ["amd", "nvidia"], 4, 0),
  # mixtral
  "mixtral.txt": (REGEXES["mixtral"], ["amd"], 3, 0),
  # gpt2
  "gpt2_unjitted.txt": (REGEXES["gpt2"], ["amd", "mac", "nvidia"], 4, 0),
  "gpt2_jitted.txt": (REGEXES["gpt2"], ["amd", "mac", "nvidia"], 4, 0),
  "gpt2_half.txt": (REGEXES["gpt2"], ["mac", "nvidia"], 4, 0),
  "gpt2_half_beam.txt": (REGEXES["gpt2"], ["mac", "nvidia"], 4, 0),
  # cifar
  "train_cifar.txt": (REGEXES["cifar"], ["amd-train", "mac", "nvidia-train"], 3, 0),
  "train_cifar_half.txt": (REGEXES["cifar"], ["amd-train", "mac", "nvidia-train"], 3, 0),
  "train_cifar_bf16.txt": (REGEXES["cifar"], ["amd-train", "nvidia-train"], 3, 0),
  "train_cifar_one_gpu.txt": (REGEXES["cifar"], ["amd-train", "nvidia-train"], 3, 20),
  "train_cifar_six_gpu.txt": (REGEXES["cifar"], ["amd-train", "nvidia-train"], 3, 20),
  # resnet
  "train_resnet_one_gpu.txt": (REGEXES["resnet"], ["amd-train", "nvidia-train"], 3, 0),
  "train_resnet.txt": (REGEXES["resnet"], ["amd-train", "nvidia-train"], 3, 0),
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
  return round(sums / counts, 2)

def regex_benchmark_to_points(regex: re.Pattern, filename: str, system: str, skip_count: int, max_count: int = 0, start: int = 0) -> list[tuple[int, float]]:
  points = []
  for run_number, benchmark in get_benchmarks(filename, system, start):
    runtime = regex_extract_benchmark(regex, benchmark, skip_count, max_count)
    points.append((run_number, runtime))
  return points

def filter_outliers_by_stddev(points: list[tuple[int, float]], stddev_multiplier: float = 2) -> list[tuple[int, float]]:
  points = sorted(points, key=lambda x: x[1])
  avg = sum(point[1] for point in points) / len(points)
  std = (sum((point[1] - avg) ** 2 for point in points) / len(points)) ** 0.5
  return [point for point in points if abs(point[1] - avg) < stddev_multiplier * std]

def filter_points(points: list[tuple[int, float]], last_n: int | None) -> list[tuple[int, float]]:
  points = [point for point in points if point[1] != -inf]
  # points = filter_outliers_by_stddev(points) if len(points) > 10 else points
  points = sorted(points, key=lambda x: x[0])
  if last_n is not None: points = points[-last_n:]
  return points

class _CachedBenchmarks:
  def __init__(self):
    self.last_run = 0
    self.cache, self.curr_commit = {}, ""
    self._update_cache()

  def _update_cache(self, force:bool=False):
    logging.info("Updating cached benchmarks.")
    if not force and (BENCHMARKS_DIR / "artifacts").stat().st_mtime <= self.last_run: return

    # update cache
    if len(self.cache) == 0 or force:
      for file, (regex, systems, skip_count, max_count) in TRACKED_BENCHMARKS.items():
        for system in systems:
          points = regex_benchmark_to_points(regex, file, system, skip_count, max_count)
          points = filter_points(points, None)
          self.cache[(file, system)] = points
    else: # only need to update the new runs
      for file, (regex, systems, skip_count, max_count) in TRACKED_BENCHMARKS.items():
        for system in systems:
          last_run = max(self.cache[(file, system)], key=lambda x: x[0])[0] if (file, system) in self.cache else 0
          points = regex_benchmark_to_points(regex, file, system, skip_count, max_count, last_run)
          points = filter_points(points, None)
          self.cache[(file, system)] += points

    # update commit
    workflow_runs = REPO.get_workflow("benchmark.yml").get_runs(branch="master", status="success", event="push")
    latest_run = int(max((BENCHMARKS_DIR / "artifacts").iterdir(), key=lambda x: int(x.name)).name)
    for run in workflow_runs:
      if run.run_number == latest_run:
        self.curr_commit = run.head_sha
        break

    self.last_run = time.time()
    logging.info(f"Cached benchmarks updated. Current commit: {self.curr_commit}")
CachedBenchmarks = _CachedBenchmarks()
