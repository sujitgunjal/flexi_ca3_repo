import csv
import json
from collections import Counter
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
EXPECTED_COLUMNS = [
    "request_id", "category", "query", "baseline_model", "gateway_model",
    "baseline_input_tokens", "gateway_input_tokens", "baseline_output_tokens",
    "gateway_output_tokens", "baseline_total_tokens", "gateway_total_tokens",
    "baseline_cost", "gateway_cost", "baseline_latency_ms", "gateway_latency_ms",
    "cache_hit", "context_before_tokens", "context_after_tokens", "quality_score",
    "quality_status", "escalated", "fallback_used",
]


def test_dataset_schema_and_category_distribution():
    with (REPO_ROOT / "evaluation" / "dataset.json").open(encoding="utf-8") as file:
        records = json.load(file)

    assert len(records) == 100
    assert [record["id"] for record in records] == list(range(1, 101))
    assert all(set(("id", "category", "query")) <= record.keys() for record in records)
    counts = Counter(record["category"] for record in records)
    assert counts == {
        "simple": 30,
        "medium": 30,
        "complex": 20,
        "coding": 10,
        "long-context": 10,
    }


def test_results_csv_has_expected_headers_only():
    with (REPO_ROOT / "evaluation" / "results.csv").open(encoding="utf-8", newline="") as file:
        rows = list(csv.reader(file))

    assert rows == [EXPECTED_COLUMNS]
