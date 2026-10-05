# Evaluation

This folder contains the fixed workload and documentation for measuring the gateway against a strong-model baseline.

- `dataset.json` contains 100 query records with an integer ID, category, and query text. Categories are simple, medium, complex, coding, and long-context.
- **Baseline:** every request goes directly to a strong model.
- **Proposed gateway:** request → cache → complexity → context optimization → model selection → LLM → quality check → escalation/fallback → response.
- `metrics.md` defines cost, token, latency, routing, cache, quality, and reliability measures.
- `results.csv` is a headers-only template; it contains no fabricated experiment results.
- `data_contract.md` describes fields future gateway components can submit to request logging.

Eventually, run each dataset query through the baseline and gateway under recorded conditions, capture the per-request measurements in `results.csv`, and summarize aggregate metrics using `metrics.md`. Person 3 owns the dataset, evaluation methodology, logging schema, and result validation.
