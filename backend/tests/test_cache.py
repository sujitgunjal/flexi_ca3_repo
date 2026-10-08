import json
import time

import pytest
from redis.exceptions import ConnectionError as RedisConnectionError

from app.cache.redis_cache import RedisCache, generate_cache_key


class MemoryRedis:
    def __init__(self):
        self.values = {}
        self.expirations = {}

    def get(self, key):
        return self.values.get(key)

    def set(self, key, value, ex):
        self.values[key] = value
        self.expirations[key] = ex

    def delete(self, key):
        return int(self.values.pop(key, None) is not None)

    def exists(self, key):
        return key in self.values


def test_json_set_get_ttl_delete_exists_and_default_ttl():
    client = MemoryRedis()
    cache = RedisCache(client, ttl=3600)
    cache.set("key", {"message": "hello"})
    assert client.expirations["key"] == 3600
    assert json.loads(client.values["key"]) == {"message": "hello"}
    assert cache.get("key") == {"message": "hello"}
    assert cache.exists("key") is True
    assert cache.delete("key") == 1
    assert cache.exists("key") is False


def test_set_allows_per_entry_ttl_and_rejects_python_objects():
    cache = RedisCache(MemoryRedis(), ttl=9)
    cache.set("key", [1, 2], ttl=3)
    assert cache.client.expirations["key"] == 3
    with pytest.raises(TypeError):
        cache.set("bad", object())


def test_key_normalizes_whitespace_but_preserves_query_meaning():
    assert generate_cache_key("  What   is Docker?\n") == generate_cache_key("What is Docker?")
    assert generate_cache_key("What is Docker?") != generate_cache_key("What is docker?")
    assert generate_cache_key("one two") != generate_cache_key("onetwo")
    assert generate_cache_key("q").startswith("llm_cache:")


def test_cache_agent_records_event_and_falls_back_on_redis_error(monkeypatch):
    from app.agents.cache_agent import CacheAgent
    from app.services import metrics_service

    class BrokenCache:
        def get(self, _key):
            raise RedisConnectionError("unavailable")

    events = []
    monkeypatch.setattr(metrics_service, "record_cache_event", lambda *args, **kwargs: events.append((args, kwargs)))
    # CacheAgent imports the callable directly, so patch its local reference too.
    import app.agents.cache_agent as agent_module
    monkeypatch.setattr(agent_module, "record_cache_event", lambda *args, **kwargs: events.append((args, kwargs)))
    state = CacheAgent(BrokenCache()).run({"query": "test", "metrics_request_id": 42})
    assert state["cache_hit"] is False
    assert state["cache_unavailable"] is True
    assert events[0][0][:2] == (42, False)
    assert events[0][1]["fallback_used"] is True


@pytest.mark.integration
def test_real_redis_connection_set_get_ttl_and_delete():
    import redis
    from app.providers.config import REDIS_DB, REDIS_HOST, REDIS_PORT

    client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB,
                         decode_responses=True, socket_connect_timeout=0.2,
                         socket_timeout=0.2)
    try:
        client.ping()
    except redis.RedisError:
        pytest.skip("Redis integration service is unavailable")
    cache = RedisCache(client)
    key = generate_cache_key(f"integration-{time.time_ns()}")
    try:
        cache.set(key, {"ok": True}, ttl=1)
        assert cache.get(key) == {"ok": True}
        assert cache.exists(key)
        assert client.ttl(key) <= 1
        time.sleep(1.05)
        assert cache.get(key) is None
        assert cache.delete(key) == 0
        assert cache.get(key) is None
    finally:
        cache.delete(key)
