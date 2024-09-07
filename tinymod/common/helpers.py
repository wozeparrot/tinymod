import os, functools

@functools.lru_cache(None)
def getenv(key:str, default=0): return type(default)(os.getenv(key, default))

class Singleton(type):
  _instances = {}
  def __call__(cls, *args, **kwargs):
    if cls not in cls._instances: cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
    return cls._instances[cls]
