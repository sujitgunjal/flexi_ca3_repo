import json
import sys

from app.decision.calibration.calibrator import ProbabilityCalibrator
from app.decision.evaluation.diagram import render_reliability_svg
from app.decision.evaluation.metrics import score_split, suggest_threshold
from app.decision.paths import DIAGRAM_PATH, PREDICTIONS_PATH, REPORT_PATH
from app.decision.schemas.decision import TASKS


def evaluate() -> dict:
    if not PREDICTIONS_PATH.exists():
        raise SystemExit(
            "No raw predictions found. Run python -m app.decision.calibration.trainer first."
        )

    predictions = json.loads(PREDICTIONS_PATH.read_text(encoding="utf-8"))
    test_rows = [
        item
        for item in predictions
        if item["split"] == "test" and item["output_valid"]
    ]
    validation_rows = [
        item
        for item in predictions
        if item["split"] == "validation" and item["output_valid"]
    ]
    if not test_rows:
        raise SystemExit("The final test split has no valid predictions.")

    calibrator = ProbabilityCalibrator.load()
    test_calibrated = [calibrator.calibrate(item["raw"]) for item in test_rows]
    validation_calibrated = [
        calibrator.calibrate(item["raw"]) for item in validation_rows
    ]
    report = {
        "split": "test",
        "count": len(test_rows),
        "calibration_applied": calibrator.fitted,
        "note": (
            "Metrics below use only the final test split. "
            "The calibrator was fit on the calibration split and was not refit here."
        ),
        "tasks": score_split(test_rows, test_calibrated),
        "suggested_confidence_threshold": _threshold_from_validation(
            validation_rows,
            validation_calibrated,
        ),
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    DIAGRAM_PATH.write_text(
        render_reliability_svg(report["tasks"]),
        encoding="utf-8",
    )
    _print_report(report)
    print(f"\nSaved {REPORT_PATH}")
    print(f"Saved {DIAGRAM_PATH}")
    return report


def _threshold_from_validation(
    records: list[dict],
    calibrated_rows: list[dict[str, dict]],
) -> float:
    if not records:
        return 0.55

    confidences = []
    correct = []
    classes = TASKS["complexity"]
    for record, calibrated in zip(records, calibrated_rows):
        probabilities = calibrated["complexity"]
        prediction = max(classes, key=lambda name: probabilities[name])
        confidences.append(probabilities[prediction])
        correct.append(prediction == record["labels"]["complexity"])

    return suggest_threshold(confidences, correct)


def _print_report(report: dict) -> None:
    print("========== TEST SET: RAW VS CALIBRATED ==========")
    print(f"Examples: {report['count']}")
    print(f"Suggested confidence threshold: {report['suggested_confidence_threshold']}")

    for task, scores in report["tasks"].items():
        raw = scores["raw"]
        calibrated = scores["calibrated"]
        print(f"\n{task}")
        print(
            f"  raw        accuracy={raw['accuracy']} "
            f"f1={raw['macro_f1']} brier={raw['brier_score']}"
        )
        print(
            f"  calibrated accuracy={calibrated['accuracy']} "
            f"f1={calibrated['macro_f1']} brier={calibrated['brier_score']}"
        )
        print(f"  raw confusion={raw['confusion_matrix']['matrix']}")
        print(f"  calibrated confusion={calibrated['confusion_matrix']['matrix']}")


def main() -> None:
    sys.stdout.reconfigure(errors="replace")
    evaluate()


if __name__ == "__main__":
    main()
