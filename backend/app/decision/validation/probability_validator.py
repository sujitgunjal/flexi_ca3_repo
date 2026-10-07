import json
import math

from app.decision.schemas.decision import TASKS


class ProbabilityValidationError(ValueError):
    """The model output is not a usable probability distribution."""


def parse_model_output(text: str) -> dict[str, dict[str, float]]:
    payload = _load_json_object(text)
    parsed: dict[str, dict[str, float]] = {}

    for task, classes in TASKS.items():
        raw = payload.get(task)
        if not isinstance(raw, dict):
            raise ProbabilityValidationError(
                f"{task} must be an object of class probabilities"
            )
        parsed[task] = normalize_distribution(raw, classes, task)

    return parsed


def normalize_distribution(
    raw: dict,
    classes: tuple[str, ...],
    task: str,
) -> dict[str, float]:
    missing = [name for name in classes if name not in raw]
    if missing:
        raise ProbabilityValidationError(
            f"{task} is missing classes: {', '.join(missing)}"
        )

    values: dict[str, float] = {}
    for name in classes:
        values[name] = _as_probability(raw[name], f"{task}.{name}")

    values = _convert_percentages(values)
    total = sum(values.values())

    if total <= 0 or not math.isfinite(total):
        raise ProbabilityValidationError(f"{task} probabilities do not sum to a usable total")

    if abs(total - 1) > 0.15:
        raise ProbabilityValidationError(
            f"{task} probabilities sum to {total:.3f}, not approximately 1"
        )

    normalized = {name: value / total for name, value in values.items()}
    return _round_distribution(normalized, classes)


def _load_json_object(text: str) -> dict:
    candidate = text.strip()
    if candidate.startswith("```"):
        candidate = candidate.strip("`")
        candidate = candidate.replace("json", "", 1).strip()

    start = candidate.find("{")
    end = candidate.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ProbabilityValidationError("Model output did not contain a JSON object")

    try:
        payload = json.loads(candidate[start : end + 1])
    except json.JSONDecodeError as exc:
        raise ProbabilityValidationError("Model output was not valid JSON") from exc

    if not isinstance(payload, dict):
        raise ProbabilityValidationError("Model output JSON must be an object")

    return payload


def _as_probability(value, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ProbabilityValidationError(f"{label} must be a number")

    number = float(value)
    if not math.isfinite(number):
        raise ProbabilityValidationError(f"{label} must be a finite number")

    return number


def _convert_percentages(values: dict[str, float]) -> dict[str, float]:
    if any(value < 0 for value in values.values()):
        raise ProbabilityValidationError("Probabilities must be between 0 and 1")

    if any(value > 1 for value in values.values()):
        if any(value > 100 for value in values.values()):
            raise ProbabilityValidationError("Probabilities must be between 0 and 1")
        values = {name: value / 100 for name, value in values.items()}

    if any(value > 1 for value in values.values()):
        raise ProbabilityValidationError("Probabilities must be between 0 and 1")

    return values


def _round_distribution(
    values: dict[str, float],
    classes: tuple[str, ...],
) -> dict[str, float]:
    rounded = {name: round(values[name], 4) for name in classes}
    drift = round(1 - sum(rounded.values()), 4)
    top = max(classes, key=lambda name: rounded[name])
    rounded[top] = round(min(1, max(0, rounded[top] + drift)), 4)
    return rounded
