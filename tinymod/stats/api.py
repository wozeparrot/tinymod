from stats.cached_benchmarks import CachedBenchmarks
from scarletio import get_event_loop
from scarletio.websocket import WebSocketServer

import logging, json

class Api:
  def __init__(self):
    self.cached_benchmarks = CachedBenchmarks()

  async def start(self):
    self.ws = await WebSocketServer(get_event_loop(), "0.0.0.0", 10000, self.handler, extra_response_headers={"Access-Control-Allow-Origin": "*"})

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
            await protocol.send("1 Invalid argument.")
            continue
          # ensure last_n is an integer
          try: last_n = int(last_n)
          except ValueError:
            await protocol.send("1 Invalid argument.")
            continue
          if last_n < 0:
            await protocol.send("1 Invalid argument.")
            continue
          logging.info(f"{protocol.remote_address} requested benchmarks for {filename} on {system} for last {last_n}.")
          benchmarks = self.cached_benchmarks.cache.get((filename, system), [])[-last_n:]
          benchmarks = [{"x": x, "y": y} for x, y in benchmarks]
          await protocol.send("0 " + json.dumps({"filename": filename, "system": system, "benchmarks": benchmarks}))
        case _:
          await protocol.send("1 Invalid command.")
