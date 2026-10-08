"""Small JSON-only Redis response cache."""

import hashlib
import json
import re
from typing import Any

import redis
from redis.exceptions import RedisError

from app.providers.config import REDIS_DB, REDIS_HOST, REDIS_PORT, REDIS_TTL


def generate_cache_key(query: str) -> str:
    """Build a stable key from a query without changing its semantics."""
    normalized = re.sub(r"\s+", " ", query.strip())
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    return f"llm_cache:{digest}"


class RedisCache:
    """Redis cache storing JSON-compatible response data only."""

    def __init__(self, client: Any | None = None, ttl: int | None = None):
        self.client = client or redis.Redis(
            host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB,
            decode_responses=True, socket_connect_timeout=1, socket_timeout=1,
        )
        self.ttl = REDIS_TTL if ttl is None else ttl

    def get(self, key: str) -> Any | None:
        value = self.client.get(key)
        return None if value is None else json.loads(value)

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        # Validate before writing so arbitrary Python objects never reach Redis.
        encoded = json.dumps(value, separators=(",", ":"), ensure_ascii=False)
        self.client.set(key, encoded, ex=self.ttl if ttl is None else ttl)

    def delete(self, key: str) -> int:
        return self.client.delete(key)

    def exists(self, key: str) -> bool:
        return bool(self.client.exists(key))


cache = RedisCache()

__all__ = ["RedisCache", "RedisError", "cache", "generate_cache_key"]
