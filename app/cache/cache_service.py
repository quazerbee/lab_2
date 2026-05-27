import json
import os
from typing import Any, Optional

import redis


class CacheService:
    def __init__(self):
        self.ttl_default = int(os.getenv("CACHE_TTL_DEFAULT", "300"))

        try:
            self.client = redis.Redis(
                host=os.getenv("REDIS_HOST", "redis"),
                port=int(os.getenv("REDIS_PORT", "6379")),
                password=os.getenv("REDIS_PASSWORD"),
                decode_responses=True,
            )
            self.client.ping()
            self.available = True
        except Exception:
            self.client = None
            self.available = False

    def get(self, key: str) -> Optional[Any]:
        if not self.available or self.client is None:
            return None

        try:
            value = self.client.get(key)
            if value is None:
                return None

            return json.loads(value)
        except Exception:
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        if not self.available or self.client is None:
            return

        try:
            self.client.setex(
                key,
                ttl or self.ttl_default,
                json.dumps(value, default=str),
            )
        except Exception:
            return

    def delete(self, key: str) -> None:
        if not self.available or self.client is None:
            return

        try:
            self.client.delete(key)
        except Exception:
            return

    def delete_by_pattern(self, pattern: str) -> None:
        if not self.available or self.client is None:
            return

        try:
            keys = list(self.client.scan_iter(match=pattern))
            if keys:
                self.client.delete(*keys)
        except Exception:
            return


cache_service = CacheService()