"""Validate the evaluation workload and print its size and category counts."""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "backend"))

from app.evaluation.dataset import (  # noqa: E402
    DEFAULT_DATASET_PATH,
    EXPECTED_CATEGORY_COUNTS,
    load_and_validate_dataset,
)


def main() -> None:
    records, counts = load_and_validate_dataset(DEFAULT_DATASET_PATH)
    print(f"Dataset size: {len(records)}")
    for category in EXPECTED_CATEGORY_COUNTS:
        print(f"{category}: {counts[category]}")


if __name__ == "__main__":
    main()
