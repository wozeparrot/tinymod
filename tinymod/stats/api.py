from scarletio import get_event_loop
from scarletio.websocket import WebSocketServer

import logging, json, ssl, os

from common.helpers import getenv
from common.benchmarks import CachedBenchmarks, ALL_SYSTEMS

API_INVALID_ARGUMENT = json.dumps({"error": "Invalid argument."})
API_INVALID_COMMAND = json.dumps({"error": "Invalid command."})

class Api:
  async def start(self):
    if not getenv("DEV", False):
      ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
      ssl_context.load_cert_chain(os.environ["STATS_API_SSL_CERT_FILE"], os.environ["STATS_API_SSL_KEY_FILE"])
      self.ws = await WebSocketServer(get_event_loop(), "0.0.0.0", 10000, self.handler, extra_response_headers={"Access-Control-Allow-Origin": "*"}, ssl=ssl_context)
    else:
      logging.warn("SSL is disabled due to running in DEV mode.")
      self.ws = await WebSocketServer(get_event_loop(), "0.0.0.0", 10000, self.handler, extra_response_headers={"Access-Control-Allow-Origin": "*"})
    await CachedBenchmarks()._update_cache()

  async def handler(self, protocol):
    logging.info(f"New connection from {protocol.remote_address}.")
    while True:
      data = await protocol.receive()
      # command handler
      cmd, *args = data.split(" ")
      match cmd:
        case "get-benchmark":
          try: filename, system, last_n = args
          except ValueError:
            await protocol.send(API_INVALID_ARGUMENT)
            continue
          # ensure last_n is an integer
          try: last_n = int(last_n)
          except ValueError:
            await protocol.send(API_INVALID_ARGUMENT)
            continue
          if last_n < 0:
            await protocol.send(API_INVALID_ARGUMENT)
            continue
          logging.info(f"{protocol.remote_address} requested benchmarks for {filename} on {system} for last {last_n}.")
          benchmarks = [[] for _ in range(len(ALL_SYSTEMS))]
          systems = system.split("_")

          # special handling
          if filename == "benchmarks.usage":
            benchmarks = [[{"x": x, "y": y} for x,y in CachedBenchmarks().benchmarks_usage]]
          elif filename == "unittests.usage":
            benchmarks = [[{"x": x, "y": y} for x,y in CachedBenchmarks().unittests_usage]]
          else:
            for system_ in systems: benchmarks[ALL_SYSTEMS.index(system_)] = CachedBenchmarks().cache.get((filename, system_), [])[-last_n:]
            benchmarks = [[{"x": x, "y": y} for x,y in benchmark] for benchmark in benchmarks]
          await protocol.send(json.dumps({"filename": filename, "system": system, "benchmarks": benchmarks}))
        case "get-curr-commit":
          await protocol.send(json.dumps({"curr-commit": CachedBenchmarks().curr_commit}))
        case "get-run-commit-map":
          await protocol.send(json.dumps({"run-commit-map": CachedBenchmarks().commit_cache}))
        case _:
          await protocol.send(API_INVALID_COMMAND)
