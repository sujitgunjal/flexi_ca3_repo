# Redis response cache

Redis is an optional cache for JSON-serializable chat responses. The application
connects using `REDIS_HOST`, `REDIS_PORT`, and `REDIS_DB`; entries expire after
`REDIS_TTL` seconds. Defaults are `localhost`, `6379`, database `0`, and `3600`
seconds. Set these in `backend/.env` (see `backend/.env.example`).

Start Redis locally with `redis-server`, or use the repository Compose setup:

```sh
docker compose up -d redis
docker compose ps redis
docker compose exec redis redis-cli ping
```

The last command should return `PONG`. Install backend dependencies from
`backend/requirements.txt` before running the application. Cache reads and writes
use the Redis client in `backend/app/cache/redis_cache.py`. If Redis is
unavailable, requests continue without caching and the request metrics record
the cache fallback. Redis stores cached responses; SQL remains the store for
request metrics, cache observations, traces, and evaluation data. Avoided
inference cost is an estimate and is reported only when model pricing and token
measurements are available.

Run cache unit and available Redis integration tests from `backend` with:

```sh
python -m pytest tests/test_cache.py -q
```

To run the four request mock-response sequence against real Redis and record its
cache events in SQL, run `python scripts/cache_simulation.py` from `backend`.

The integration test is skipped when Redis is not reachable. The cache lookup
uses SHA-256 over a query with surrounding and repeated whitespace normalized;
case and punctuation are preserved.
