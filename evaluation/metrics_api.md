# Metrics logging API

The FastAPI backend exposes provider-independent request logging backed by `RequestLog`.

## Log a request

`POST /metrics/log` accepts the query plus any measurements already available. All measurement fields are optional, so early pipeline stages can submit only `query`, `complexity`, and `selected_model`.

```json
{
  "query": "Explain Docker",
  "complexity": "simple",
  "selected_model": "cheap-model",
  "input_tokens": 100,
  "output_tokens": 150,
  "latency_ms": 500,
  "cache_hit": false
}
```

Successful response (`201`):

```json
{"success": true, "request_id": 1}
```

Example application call:

```python
from app.services.metrics_service import log_request

record = log_request({
    "query": query,
    "complexity": complexity,
    "selected_model": model,
    "input_tokens": input_tokens,
    "output_tokens": output_tokens,
    "latency_ms": latency,
    "cache_hit": cache_hit,
})
print(record.id)
```

## Retrieve metrics

- `GET /metrics/recent` returns the latest 100 records, newest first.
- `GET /metrics/{request_id}` returns one record or `404` when it is missing.
- `GET /metrics/summary` returns aggregate metrics.

## Fields and calculations

The request accepts `query`, `complexity`, `selected_model`, `final_model`, `input_tokens`, `output_tokens`, `total_tokens`, `latency_ms`, `estimated_cost`, `cache_hit`, `context_before_tokens`, `context_after_tokens`, `context_reduction_percent`, `quality_score`, `quality_status`, `escalated`, and `fallback_used`. Only `query` is required. Token counts, latency, and cost must be non-negative; quality score is from 1 to 5.

When both input and output counts exist, total tokens are their sum unless the caller supplied `total_tokens`. Context reduction is `((before - after) / before) * 100`; when `before` is zero, it is `0`. Explicit values for derived fields are preserved.

The cost utility uses configurable rates per million tokens. Current values are clearly marked demo placeholders in `backend/app/services/cost_service.py`, not real provider prices. Unknown models or missing token counts produce no calculated cost. A supplied `estimated_cost` is kept.

The summary reports request count, summed known token counts, means over recorded latency/cost/quality values, cache hit count and hit rate (`cache hits / all logged requests`), escalation and fallback counts, and usage counts grouped by final model when available, otherwise selected model. Missing optional values do not invent measurements; an empty dataset returns zero counts/means and a null quality average.
