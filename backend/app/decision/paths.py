from pathlib import Path


DECISION_ROOT = Path(__file__).resolve().parent
DATASET_PATH = DECISION_ROOT / "calibration" / "dataset.json"
ARTIFACT_DIR = DECISION_ROOT / "calibration" / "artifacts"
CALIBRATOR_PATH = ARTIFACT_DIR / "calibrator.json"
PREDICTIONS_PATH = ARTIFACT_DIR / "raw_predictions.json"
REPORT_PATH = ARTIFACT_DIR / "evaluation_report.json"
DIAGRAM_PATH = ARTIFACT_DIR / "reliability.svg"
RULES_PATH = DECISION_ROOT / "routing" / "rules.json"
