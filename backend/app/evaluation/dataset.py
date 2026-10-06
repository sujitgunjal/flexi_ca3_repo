"""Validation helpers for the fixed evaluation query dataset."""

import json
from collections import Counter
from pathlib import Path
from typing import Any


VALID_CATEGORIES = {"simple", "medium", "complex", "coding", "long-context"}
EXPECTED_CATEGORY_COUNTS = {
    "simple": 30,
    "medium": 30,
    "complex": 20,
    "coding": 10,
    "long-context": 10,
}
DEFAULT_DATASET_PATH = Path(__file__).resolve().parents[3] / "evaluation" / "dataset.json"


def load_and_validate_dataset(path: str | Path = DEFAULT_DATASET_PATH) -> tuple[list[dict[str, Any]], Counter[str]]:
    """Load JSON and verify IDs, query text, categories, and expected size."""
    dataset_path = Path(path)
    try:
        with dataset_path.open(encoding="utf-8") as file:
            records = json.load(file)
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Could not load valid JSON dataset at {dataset_path}: {exc}") from exc
    if not isinstance(records, list):
        raise ValueError("Dataset root must be a JSON array")

    ids: list[int | str] = []
    categories: list[str] = []
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise ValueError(f"Record {index + 1} must be a JSON object")
        if "id" not in record or "category" not in record or "query" not in record:
            raise ValueError(f"Record {index + 1} must contain id, category, and query")
        if isinstance(record["id"], bool) or not isinstance(record["id"], (int, str)):
            raise ValueError(f"Record {index + 1} ID must be an integer or string")
        if not isinstance(record["query"], str) or not record["query"].strip():
            raise ValueError(f"Record {index + 1} query must be non-empty")
        if not isinstance(record["category"], str) or record["category"] not in VALID_CATEGORIES:
            raise ValueError(f"Record {index + 1} has invalid category: {record['category']!r}")
        ids.append(record["id"])
        categories.append(record["category"])

    if len(ids) != len(set(ids)):
        raise ValueError("Dataset IDs must be unique")
    counts = Counter(categories)
    missing = VALID_CATEGORIES - counts.keys()
    if missing:
        raise ValueError(f"Dataset is missing expected categories: {', '.join(sorted(missing))}")
    if not 90 <= len(records) <= 110:
        raise ValueError(f"Expected approximately 100 records; found {len(records)}")
    return records, counts
