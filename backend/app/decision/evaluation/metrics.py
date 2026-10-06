from app.decision.schemas.decision import TASKS


def classification_report(
    labels: list[str],
    predictions: list[str],
    classes: tuple[str, ...],
) -> dict:
    matrix = [
        [0 for _ in classes]
        for _ in classes
    ]
    index = {name: position for position, name in enumerate(classes)}

    for truth, predicted in zip(labels, predictions):
        matrix[index[truth]][index[predicted]] += 1

    per_class = []
    for position, name in enumerate(classes):
        true_positive = matrix[position][position]
        false_positive = sum(matrix[row][position] for row in range(len(classes))) - true_positive
        false_negative = sum(matrix[position]) - true_positive
        support = sum(matrix[position])
        precision = _ratio(true_positive, true_positive + false_positive)
        recall = _ratio(true_positive, true_positive + false_negative)
        per_class.append(
            {
                "label": name,
                "precision": precision,
                "recall": recall,
                "f1": _f1(precision, recall),
                "support": support,
            }
        )

    correct = sum(matrix[position][position] for position in range(len(classes)))
    return {
        "accuracy": _ratio(correct, len(labels)),
        "macro_precision": _mean([item["precision"] for item in per_class]),
        "macro_recall": _mean([item["recall"] for item in per_class]),
        "macro_f1": _mean([item["f1"] for item in per_class]),
        "confusion_matrix": {
            "labels": list(classes),
            "matrix": matrix,
        },
        "per_class": per_class,
    }


def brier_score(
    probability_rows: list[dict[str, float]],
    labels: list[str],
    classes: tuple[str, ...],
) -> float:
    if not probability_rows:
        return 0.0

    total = 0.0
    for probabilities, label in zip(probability_rows, labels):
        total += sum(
            (probabilities[class_name] - (1.0 if class_name == label else 0.0)) ** 2
            for class_name in classes
        )
    return round(total / len(probability_rows), 4)


def reliability_bins(
    confidences: list[float],
    correct: list[bool],
    bins: int = 5,
) -> list[dict]:
    width = 1 / bins
    rows = []

    for index in range(bins):
        lower = index * width
        upper = 1 if index == bins - 1 else (index + 1) * width
        selected = [
            (confidence, was_correct)
            for confidence, was_correct in zip(confidences, correct)
            if (lower <= confidence < upper) or (index == bins - 1 and confidence == 1)
        ]
        if not selected:
            rows.append(
                {
                    "lower": round(lower, 2),
                    "upper": round(upper, 2),
                    "count": 0,
                    "mean_confidence": None,
                    "accuracy": None,
                }
            )
            continue

        mean_confidence = sum(item[0] for item in selected) / len(selected)
        accuracy = sum(1 for item in selected if item[1]) / len(selected)
        rows.append(
            {
                "lower": round(lower, 2),
                "upper": round(upper, 2),
                "count": len(selected),
                "mean_confidence": round(mean_confidence, 4),
                "accuracy": round(accuracy, 4),
            }
        )

    return rows


def suggest_threshold(
    confidences: list[float],
    correct: list[bool],
) -> float:
    """Lowest threshold on the validation set whose accuracy is at least 0.75."""

    best = 0.55
    for threshold in (0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80):
        chosen = [
            was_correct
            for confidence, was_correct in zip(confidences, correct)
            if confidence >= threshold
        ]
        if len(chosen) < 3:
            continue
        accuracy = sum(1 for item in chosen if item) / len(chosen)
        if accuracy >= 0.75:
            return threshold
        best = threshold

    return best


def score_split(records: list[dict], calibrated_rows: list[dict[str, dict]]) -> dict:
    report = {}

    for task, classes in TASKS.items():
        labels = [record["labels"][task] for record in records]
        raw_probabilities = [record["raw"][task] for record in records]
        calibrated_probabilities = [row[task] for row in calibrated_rows]
        raw_predictions = [_argmax(probabilities, classes) for probabilities in raw_probabilities]
        calibrated_predictions = [
            _argmax(probabilities, classes)
            for probabilities in calibrated_probabilities
        ]
        raw_confidence = [
            probabilities[prediction]
            for probabilities, prediction in zip(raw_probabilities, raw_predictions)
        ]
        calibrated_confidence = [
            probabilities[prediction]
            for probabilities, prediction in zip(
                calibrated_probabilities,
                calibrated_predictions,
            )
        ]
        raw_correct = [
            prediction == label
            for prediction, label in zip(raw_predictions, labels)
        ]
        calibrated_correct = [
            prediction == label
            for prediction, label in zip(calibrated_predictions, labels)
        ]

        report[task] = {
            "raw": {
                **classification_report(labels, raw_predictions, classes),
                "brier_score": brier_score(raw_probabilities, labels, classes),
                "reliability": reliability_bins(raw_confidence, raw_correct),
            },
            "calibrated": {
                **classification_report(labels, calibrated_predictions, classes),
                "brier_score": brier_score(calibrated_probabilities, labels, classes),
                "reliability": reliability_bins(
                    calibrated_confidence,
                    calibrated_correct,
                ),
            },
        }

    return report


def _argmax(probabilities: dict[str, float], classes: tuple[str, ...]) -> str:
    return max(classes, key=lambda name: probabilities[name])


def _ratio(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return round(numerator / denominator, 4)


def _f1(precision: float, recall: float) -> float:
    if precision + recall == 0:
        return 0.0
    return round(2 * precision * recall / (precision + recall), 4)


def _mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return round(sum(values) / len(values), 4)
