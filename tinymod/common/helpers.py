import os, functools, multiprocessing

@functools.lru_cache(None)
def getenv(key:str, default=0): return type(default)(os.getenv(key, default))

class Singleton:
  _instance = None
  _lock = multiprocessing.Lock()
  def __new__(cls):
    if cls._instance is None:
      with cls._lock:
        if not cls._instance: cls._instance = super().__new__(cls)
    return cls._instance
