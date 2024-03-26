import zipfile, re
from pathlib import Path
from math import inf

BENCHMARKS_DIR = Path("persist/benchmarks")
def get_benchmarks(filename: str, system: str):
  for path in (BENCHMARKS_DIR / "artifacts").iterdir():
    if not path.is_dir(): continue
    if not (path / f"{system}.zip").exists(): continue
    with zipfile.ZipFile(path / f"{system}.zip") as zip:
      if filename not in zip.namelist(): continue
      with zip.open(filename) as f:
        yield int(path.name), f.read().decode()

REGEXES = {
  "sd": re.compile(r"step in (\d+\.\d+) ms"),
  "llama": re.compile(r"total (\d+\.\d+) ms"),
  "gpt2": re.compile(r"ran model in[ ]+(\d+\.\d+) ms"),
  "cifar": re.compile(r"\d+[ ]+(\d+\.\d+) ms run,"),
  "resnet": re.compile(r"\d+[ ]+(\d+\.\d+) ms run,"),
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

def regex_benchmark_to_points(regex: re.Pattern, filename: str, system: str, skip_count: int, max_count: int = 0) -> list[tuple[int, float]]:
  points = []
  for run_number, benchmark in get_benchmarks(filename, system):
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
  points = filter_outliers_by_stddev(points) if len(points) > 10 else points
  points = sorted(points, key=lambda x: x[0])
  if last_n is not None: points = points[-last_n:]
  return points
