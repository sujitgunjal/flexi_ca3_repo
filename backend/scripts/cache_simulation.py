"""Exercise the real Redis response cache with deterministic mock responses."""

from uuid import uuid4

from app.cache.redis_cache import RedisError, cache, generate_cache_key
from app.services.metrics_service import log_request, record_cache_event


def run_simulation() -> dict[str, int | float]:
    requests = ["What is Docker?", "What is Docker?", "Explain Kubernetes", "What is Docker?"]
    counts = {"total_requests": 0, "cache_hits": 0, "cache_misses": 0}
    run_namespace = uuid4().hex
    keys = [f"cache_sim:{run_namespace}:{generate_cache_key(query)}" for query in set(requests)]
    try:
        for key in keys:
            cache.delete(key)
    except RedisError as exc:
        raise RuntimeError("Redis must be running to execute this simulation") from exc
    for query in requests:
        key = f"cache_sim:{run_namespace}:{generate_cache_key(query)}"
        record = log_request({"query": query})
        counts["total_requests"] += 1
        try:
            response = cache.get(key)
        except RedisError as exc:
            raise RuntimeError("Redis must be running to execute this simulation") from exc
        hit = response is not None
        record_cache_event(record.id, hit, key)
        if hit:
            counts["cache_hits"] += 1
        else:
            counts["cache_misses"] += 1
            cache.set(key, {"response": f"Simulated answer for: {query}"})
    counts["cache_hit_rate"] = counts["cache_hits"] / counts["total_requests"]
    counts["api_calls_avoided"] = counts["cache_hits"]
    for key in keys:
        cache.delete(key)
    return counts


if __name__ == "__main__":
    print(run_simulation())
