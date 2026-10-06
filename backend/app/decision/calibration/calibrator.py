import json
from pathlib import Path

from app.decision.paths import CALIBRATOR_PATH
from app.decision.schemas.decision import TASKS
from app.decision.validation.probability_validator import _round_distribution


class ProbabilityCalibrator:
    """Post-hoc one-vs-rest isotonic regression.

    This module never calls the decision model. It only remaps probabilities
    that were already produced and validated.
    """

    def __init__(self, artifact: dict | None = None):
        self.artifact = artifact or {
            "method": "identity",
            "fitted": False,
            "tasks": {},
        }

    @property
    def fitted(self) -> bool:
        return bool(self.artifact.get("fitted"))

    @classmethod
    def load(cls, path: Path | None = None) -> "ProbabilityCalibrator":
        artifact_path = path or CALIBRATOR_PATH
        if not artifact_path.exists():
            return cls()

        return cls(json.loads(artifact_path.read_text(encoding="utf-8")))

    def save(self, path: Path | None = None) -> Path:
        artifact_path = path or CALIBRATOR_PATH
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_text(
            json.dumps(self.artifact, indent=2),
            encoding="utf-8",
        )
        return artifact_path

    def calibrate(self, raw: dict[str, dict[str, float]]) -> dict[str, dict[str, float]]:
        calibrated: dict[str, dict[str, float]] = {}

        for task, classes in TASKS.items():
            probabilities = raw[task]
            if not self.fitted:
                calibrated[task] = dict(probabilities)
                continue

            models = self.artifact.get("tasks", {}).get(task, {})
            scored = {
                class_name: _predict_isotonic(
                    models.get(class_name, []),
                    probabilities[class_name],
                )
                for class_name in classes
            }
            calibrated[task] = _renormalize(scored, classes)

        return calibrated


def fit_isotonic_calibrator(
    samples: list[dict],
) -> ProbabilityCalibrator:
    """Fit one isotonic model per class from calibration-split samples.

    Each sample needs "raw" probabilities and "labels".
    """

    tasks: dict[str, dict[str, list[dict]]] = {}

    for task, classes in TASKS.items():
        tasks[task] = {}
        for class_name in classes:
            xs: list[float] = []
            ys: list[float] = []
            for sample in samples:
                xs.append(float(sample["raw"][task][class_name]))
                ys.append(1.0 if sample["labels"][task] == class_name else 0.0)
            tasks[task][class_name] = _fit_isotonic(xs, ys)

    return ProbabilityCalibrator(
        {
            "method": "isotonic_regression_ovr",
            "fitted": True,
            "description": (
                "One-vs-rest isotonic regression fitted on the calibration split only."
            ),
            "tasks": tasks,
        }
    )


def _fit_isotonic(xs: list[float], ys: list[float]) -> list[dict]:
    grouped: dict[float, list[float]] = {}
    for raw_x, raw_y in zip(xs, ys):
        x_value = round(min(1.0, max(0.0, raw_x)), 6)
        grouped.setdefault(x_value, []).append(raw_y)

    points = [
        (x_value, sum(values) / len(values), len(values))
        for x_value, values in sorted(grouped.items())
    ]
    blocks: list[list[float]] = []

    for x_value, mean_y, weight in points:
        blocks.append([x_value, x_value, mean_y * weight, float(weight)])
        while len(blocks) >= 2:
            left_mean = blocks[-2][2] / blocks[-2][3]
            right_mean = blocks[-1][2] / blocks[-1][3]
            if left_mean <= right_mean + 1e-12:
                break
            left = blocks[-2]
            right = blocks[-1]
            blocks = blocks[:-2] + [[
                left[0],
                right[1],
                left[2] + right[2],
                left[3] + right[3],
            ]]

    return [
        {
            "x_min": round(block[0], 6),
            "x_max": round(block[1], 6),
            "y": round(min(1.0, max(0.0, block[2] / block[3])), 6),
        }
        for block in blocks
    ]


def _predict_isotonic(blocks: list[dict], raw_probability: float) -> float:
    if not blocks:
        return min(1.0, max(0.0, raw_probability))

    x_value = min(1.0, max(0.0, raw_probability))
    if x_value <= blocks[0]["x_max"]:
        return float(blocks[0]["y"])

    for index in range(1, len(blocks)):
        left = blocks[index - 1]
        right = blocks[index]
        if x_value > right["x_max"]:
            continue
        if x_value >= right["x_min"]:
            return float(right["y"])

        span = right["x_min"] - left["x_max"]
        if span <= 1e-9:
            return float(right["y"])

        weight = (x_value - left["x_max"]) / span
        return float(left["y"] + weight * (right["y"] - left["y"]))

    return float(blocks[-1]["y"])


def _renormalize(
    values: dict[str, float],
    classes: tuple[str, ...],
) -> dict[str, float]:
    clipped = {name: min(1.0, max(0.0, values[name])) for name in classes}
    total = sum(clipped.values())
    if total <= 0:
        uniform = 1 / len(classes)
        clipped = {name: uniform for name in classes}
    else:
        clipped = {name: value / total for name, value in clipped.items()}

    return _round_distribution(clipped, classes)
