from typing import Any, Optional
from datetime import datetime, timedelta

from core import settings


class SimpleCache:
    """
    Cache implementation that stores the data in memory to lower the db queries and query time.
    Loads cache memory at the same time.
    """
    def __init__(self):
        self._cache = {}

    async def set(self, key: str, value: Any, expire: int = settings.cache.objects_cache_sec):
        expiry = datetime.now() + timedelta(seconds=expire)
        self._cache[key] = (value, expiry)

    async def get(self, key: str) -> Optional[Any]:
        if key in self._cache:
            value, expiry = self._cache[key]
            if datetime.now() < expiry:
                return value
            else:
                del self._cache[key]
        return None


cache = SimpleCache()
