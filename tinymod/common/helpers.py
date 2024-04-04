import os, functools

@functools.lru_cache(None)
def getenv(key:str, default=0): return type(default)(os.getenv(key, default))
