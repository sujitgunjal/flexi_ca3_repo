# Evaluation

This directory contains the fixed workload and documentation for comparing a strong-model baseline with the proposed gateway.

- `dataset.json` contains 100 query records across simple, medium, complex, coding, and long-context categories.
- `results.csv` is a headers-only baseline-versus-gateway template. No experiment results have been added.
- `metrics.md` defines the evaluation measures; `data_contract.md` documents fields available to the logging layer.
- `metrics_api.md` documents the Day 2 request logging and retrieval API.
- `run_evaluation.py` validates the dataset and prints its size and category counts. It does not call LLMs or create experiment results.

Run the lightweight dataset check from the repository root:

```bash
python evaluation/run_evaluation.py
```

For actual future experiments, run each query through both paths under recorded conditions, then add measured per-request observations to `results.csv`. Do not interpret the empty template as experimental results.
