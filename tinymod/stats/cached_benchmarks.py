import time, logging

from common.benchmarks import regex_benchmark_to_points, filter_points, BENCHMARKS_DIR, REGEXES, REPO

# regex, systems, skip_count, max_count
TRACKED_BENCHMARKS = {
  "sd.txt": (REGEXES["sd"], ["amd", "mac"], 3, 0),
  "llama_unjitted.txt": (REGEXES["llama"], ["amd", "mac"], 3, 0),
  "llama_jitted.txt": (REGEXES["llama"], ["amd", "mac"], 3, 0),
  "gpt2_unjitted.txt": (REGEXES["gpt2"], ["amd", "mac", "nvidia"], 3, 0),
  "gpt2_jitted.txt": (REGEXES["gpt2"], ["amd", "mac", "nvidia"], 3, 0),
  "gpt2_half_beam.txt": (REGEXES["gpt2"], ["nvidia"], 3, 0),
  "train_cifar_one_gpu.txt": (REGEXES["cifar"], ["amd-train"], 3, 20),
  "train_cifar_six_gpu.txt": (REGEXES["cifar"], ["amd-train"], 3, 20),
  "train_resnet_one_gpu.txt": (REGEXES["resnet"], ["amd-train"], 3, 0),
  "train_resnet.txt": (REGEXES["resnet"], ["amd-train"], 3, 0),
}

class CachedBenchmarks:
  def __init__(self):
    self.last_run = 0
    self.cache, self.curr_commit = {}, ""
    self._update_cache()

  def _update_cache(self, force:bool=False):
    if not force and BENCHMARKS_DIR.stat().st_mtime <= self.last_run: return

    # update cache
    for file, (regex, systems, skip_count, max_count) in TRACKED_BENCHMARKS.items():
      for system in systems:
        points = regex_benchmark_to_points(regex, file, system, skip_count, max_count)
        points = filter_points(points, None)
        self.cache[(file, system)] = points

    # update commit
    workflow_runs = REPO.get_workflow("benchmark.yml").get_runs(branch="master", status="success", event="push")
    latest_run = int(max((BENCHMARKS_DIR / "artifacts").iterdir(), key=lambda x: int(x.name)).name)
    for run in workflow_runs:
      if run.run_number == latest_run:
        self.curr_commit = run.head_sha
        break

    self.last_run = time.time()
    logging.info(f"Cached benchmarks updated. Current commit: {self.curr_commit}")
