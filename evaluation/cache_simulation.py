"""Small in-memory cache metrics demonstration; no production cache involved."""


def simulate_cache_metrics(queries: list[str] | None = None) -> dict[str, int | float]:
    queries = queries or ["Query A", "Query B", "Query A", "Query C", "Query B", "Query A"]
    seen: set[str] = set()
    hits = 0
    for query in queries:
        if query in seen:
            hits += 1
        else:
            seen.add(query)
    total = len(queries)
    return {"total_requests": total, "cache_hits": hits, "cache_misses": total - hits,
            "cache_hit_rate": hits / total if total else 0, "api_calls_avoided": hits}


if __name__ == "__main__":
    print(simulate_cache_metrics())
