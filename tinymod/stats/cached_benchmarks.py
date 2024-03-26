import time, logging

from common.benchmarks import regex_benchmark_to_points, filter_points, BENCHMARKS_DIR
from common.benchmarks import REGEXES

# regex, systems, skip_count, max_count
TRACKED_BENCHMARKS = {
  "sd.txt": (REGEXES["sd"], ["amd", "mac"], 3, 0),
  "llama_unjitted.txt": (REGEXES["llama"], ["amd", "mac"], 3, 0),
  "llama_jitted.txt": (REGEXES["llama"], ["amd", "mac"], 3, 0),
  "gpt2_unjitted.txt": (REGEXES["gpt2"], ["amd", "mac", "nvidia"], 3, 0),
  "gpt2_jitted.txt": (REGEXES["gpt2"], ["amd", "mac", "nvidia"], 3, 0),
  "gpt2_half_beam.txt": (REGEXES["gpt2"], ["nvidia"], 3, 0),
}

class CachedBenchmarks:
  def __init__(self):
    self.cache, self.last_run = {}, 0
    self._update_cache()

  def _update_cache(self, force:bool=False):
    if not force and BENCHMARKS_DIR.stat().st_mtime <= self.last_run: return
    for file, (regex, systems, skip_count, max_count) in TRACKED_BENCHMARKS.items():
      for system in systems:
        points = regex_benchmark_to_points(regex, file, system, skip_count, max_count)
        points = filter_points(points, None)
        self.cache[(file, system)] = points
    self.last_run = time.time()
    logging.info("Cached benchmarks updated.")
