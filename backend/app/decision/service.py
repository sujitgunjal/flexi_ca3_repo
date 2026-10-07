from uuid import uuid4

from app.decision.base import DecisionProvider, DecisionProviderError
from app.decision.calibration.calibrator import ProbabilityCalibrator
from app.decision.providers import get_decision_provider
from app.decision.routing.policy import RoutingPolicy
from app.decision.schemas.decision import TASKS, DecisionResponse, DecisionScore
from app.decision.validation.probability_validator import (
    ProbabilityValidationError,
    parse_model_output,
)


_CALIBRATOR: ProbabilityCalibrator | None = None
_CALIBRATOR_MTIME: float | None = None


class DecisionService:
    """query -> provider -> validation -> calibration -> routing.

    This service never generates the user-facing answer.
    """

    def __init__(
        self,
        provider: DecisionProvider | None = None,
        calibrator: ProbabilityCalibrator | None = None,
        policy: RoutingPolicy | None = None,
    ):
        self.provider = provider or get_decision_provider()
        self.calibrator = calibrator if calibrator is not None else get_calibrator()
        self.policy = policy or RoutingPolicy()
        self._reload_calibrator = calibrator is None

    def decide(self, query: str, request_id: str | None = None) -> DecisionResponse:
        if self._reload_calibrator:
            self.calibrator = get_calibrator()
        raw, output_valid = self._classify(query)
        calibrated = self.calibrator.calibrate(raw) if output_valid else raw
        scores = {
            task: _score(task, raw[task], calibrated[task])
            for task in TASKS
        }
        routing = self.policy.route(scores)
        fallback_used = not output_valid
        if fallback_used:
            routing.reason = (
                "The decision model output was invalid, so a uniform fallback "
                f"was used. {routing.reason}"
            )

        print(
            "[Decision] "
            f"provider={self.provider.name} "
            f"complexity={scores['complexity'].label} "
            f"raw_confidence={scores['complexity'].raw_confidence:.2f} "
            f"calibrated_confidence={scores['complexity'].calibrated_confidence:.2f} "
            f"uncertain={routing.uncertain} "
            f"model={routing.selected_model}"
        )

        return DecisionResponse(
            request_id=request_id or str(uuid4()),
            query=query,
            provider=self.provider.name,
            decision_model=self.provider.model_name,
            output_valid=output_valid,
            calibration_applied=self.calibrator.fitted and output_valid,
            complexity=scores["complexity"],
            reasoning=scores["reasoning"],
            context=scores["context"],
            uncertain=routing.uncertain or fallback_used,
            fallback_used=fallback_used,
            selected_model=routing.selected_model,
            routing_reason=routing.reason,
        )

    def _classify(self, query: str) -> tuple[dict[str, dict[str, float]], bool]:
        raw_text = self.provider.classify_raw(query)
        try:
            return parse_model_output(raw_text), True
        except ProbabilityValidationError as exc:
            correction = (
                f"{exc}. Return only the corrected JSON object. "
                "Each decision must sum to 1 and must not be all zeros. "
                "Do not answer the query."
            )

        corrected = self.provider.classify_raw(query, correction=correction)
        try:
            return parse_model_output(corrected), True
        except ProbabilityValidationError:
            return _uniform_distributions(), False
        except DecisionProviderError:
            raise


def get_calibrator(force_reload: bool = False) -> ProbabilityCalibrator:
    global _CALIBRATOR, _CALIBRATOR_MTIME

    from app.decision.paths import CALIBRATOR_PATH

    mtime = CALIBRATOR_PATH.stat().st_mtime if CALIBRATOR_PATH.exists() else None
    if force_reload or _CALIBRATOR is None or mtime != _CALIBRATOR_MTIME:
        _CALIBRATOR = ProbabilityCalibrator.load()
        _CALIBRATOR_MTIME = mtime
    return _CALIBRATOR


def _score(
    task: str,
    raw: dict[str, float],
    calibrated: dict[str, float],
) -> DecisionScore:
    classes = TASKS[task]
    raw_label = max(classes, key=lambda name: raw[name])
    calibrated_label = max(classes, key=lambda name: calibrated[name])

    return DecisionScore(
        label=calibrated_label,
        raw_probabilities=raw,
        raw_confidence=raw[raw_label],
        calibrated_probabilities=calibrated,
        calibrated_confidence=calibrated[calibrated_label],
    )


def _uniform_distributions() -> dict[str, dict[str, float]]:
    distributions: dict[str, dict[str, float]] = {}
    for task, classes in TASKS.items():
        share = round(1 / len(classes), 4)
        distributions[task] = {name: share for name in classes}
        drift = round(1 - sum(distributions[task].values()), 4)
        distributions[task][classes[0]] = round(
            distributions[task][classes[0]] + drift,
            4,
        )
    return distributions
