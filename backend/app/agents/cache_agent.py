import logging
from time import perf_counter

from redis.exceptions import RedisError

from app.cache.redis_cache import cache, generate_cache_key
from app.orchestration.state import RequestState
from app.services.metrics_service import record_cache_event

logger = logging.getLogger(__name__)


class CacheAgent:
    def __init__(self, cache_service=cache):
        self.cache = cache_service

    def run(self, state: RequestState) -> RequestState:
        key = generate_cache_key(state.get("query", ""))
        state["cache_key"] = key
        started = perf_counter()
        hit = False
        try:
            value = self.cache.get(key)
            hit = value is not None
            if hit:
                state.update(value)
                state["cached_response"] = True
            state["cache_unavailable"] = False
        except RedisError:
            state["cache_unavailable"] = True
            logger.exception("Redis cache unavailable; continuing without cache")
        latency_ms = (perf_counter() - started) * 1000
        state["cache_hit"] = hit

        request_id = state.get("metrics_request_id")
        if request_id is not None:
            record_cache_event(request_id, hit, key, latency_ms,
                               fallback_used=state["cache_unavailable"])

        return state
