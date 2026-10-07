import sys

from app.decision.base import DecisionProviderError
from app.decision.calibration.calibrator import (
    ProbabilityCalibrator,
    fit_isotonic_calibrator,
)
from app.decision.providers.jev_provider import JevDecisionProvider
from app.decision.routing.policy import RoutingPolicy
from app.decision.schemas.decision import DecisionScore
from app.decision.service import DecisionService
from app.decision.validation.probability_validator import (
    ProbabilityValidationError,
    parse_model_output,
)


sys.stdout.reconfigure(errors="replace")


class ScriptedProvider:
    name = "scripted"
    model_name = "scripted"

    def __init__(self, outputs: list[str]):
        self.outputs = list(outputs)

    def classify_raw(self, query: str, *, correction: str | None = None) -> str:
        if not self.outputs:
            raise AssertionError("provider called more times than expected")
        return self.outputs.pop(0)


def valid_json() -> str:
    return """
    {
      "complexity": {"simple": 0.8, "medium": 0.15, "complex": 0.05},
      "reasoning": {"low": 0.7, "medium": 0.2, "high": 0.1},
      "context": {"low": 0.6, "medium": 0.3, "high": 0.1}
    }
    """


def check(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


parsed = parse_model_output(valid_json())
check(parsed["complexity"]["simple"] == 0.8, "valid probabilities were not kept")

percent = parse_model_output(
    """
    {
      "complexity": {"simple": 70, "medium": 20, "complex": 10},
      "reasoning": {"low": 60, "medium": 30, "high": 10},
      "context": {"low": 50, "medium": 40, "high": 10}
    }
    """
)
check(abs(sum(percent["complexity"].values()) - 1) < 0.001, "percentages were not normalized")

try:
    parse_model_output('{"complexity": "simple"}')
    raise SystemExit("malformed output should have failed")
except ProbabilityValidationError:
    pass

samples = []
for index in range(10):
    correct = index < 4
    samples.append(
        {
            "raw": {
                "complexity": {"simple": 0.8, "medium": 0.1, "complex": 0.1},
                "reasoning": {"low": 0.8, "medium": 0.1, "high": 0.1},
                "context": {"low": 0.8, "medium": 0.1, "high": 0.1},
            },
            "labels": {
                "complexity": "simple" if correct else "medium",
                "reasoning": "low" if correct else "medium",
                "context": "low" if correct else "medium",
            },
        }
    )

calibrator = fit_isotonic_calibrator(samples)
calibrated = calibrator.calibrate(samples[0]["raw"])
check(
    calibrated["complexity"]["simple"] < samples[0]["raw"]["complexity"]["simple"],
    "calibration did not reduce an overconfident probability",
)

service = DecisionService(
    provider=ScriptedProvider([valid_json()]),
    calibrator=ProbabilityCalibrator(),
    policy=RoutingPolicy(),
)
decision = service.decide("What is a variable?")
check(decision.provider == "scripted", "provider name was not preserved")
check(decision.selected_model == "local", f"expected local, got {decision.selected_model}")
check(decision.complexity.raw_confidence == 0.8, "raw confidence was overwritten")
check(
    decision.complexity.calibrated_confidence == decision.complexity.raw_confidence,
    "an unfitted calibrator should keep confidence unchanged and still report it separately",
)
check(decision.calibration_applied is False, "identity calibration should be marked as not applied")
check("answer" not in decision.model_dump(), "decision response must not include a generated answer")

fallback = DecisionService(
    provider=ScriptedProvider(["The answer is 42.", "Still not JSON"]),
    calibrator=calibrator,
).decide("What is 2 + 2?")
check(fallback.output_valid is False, "invalid output was accepted")
check(fallback.uncertain is True, "invalid output should be uncertain")
check(fallback.fallback_used is True, "fallback was not recorded")

try:
    JevDecisionProvider(api_key="", api_base="").classify_raw("hello")
    raise SystemExit("unconfigured Jev should fail")
except DecisionProviderError as exc:
    check("optional" in str(exc).lower(), "Jev error should say it is optional")

high_confidence = DecisionScore(
    label="complex",
    raw_probabilities={"simple": 0.05, "medium": 0.15, "complex": 0.8},
    raw_confidence=0.8,
    calibrated_probabilities={"simple": 0.05, "medium": 0.15, "complex": 0.8},
    calibrated_confidence=0.8,
)
medium_score = DecisionScore(
    label="medium",
    raw_probabilities={"low": 0.1, "medium": 0.8, "high": 0.1},
    raw_confidence=0.8,
    calibrated_probabilities={"low": 0.1, "medium": 0.8, "high": 0.1},
    calibrated_confidence=0.8,
)
low_context = DecisionScore(
    label="low",
    raw_probabilities={"low": 0.8, "medium": 0.1, "high": 0.1},
    raw_confidence=0.8,
    calibrated_probabilities={"low": 0.8, "medium": 0.1, "high": 0.1},
    calibrated_confidence=0.8,
)
uncertain_score = DecisionScore(
    label="simple",
    raw_probabilities={"simple": 0.4, "medium": 0.35, "complex": 0.25},
    raw_confidence=0.4,
    calibrated_probabilities={"simple": 0.4, "medium": 0.35, "complex": 0.25},
    calibrated_confidence=0.4,
)
route = RoutingPolicy().route(
    {
        "complexity": uncertain_score,
        "reasoning": uncertain_score.model_copy(
            update={
                "label": "low",
                "raw_probabilities": {"low": 0.4, "medium": 0.35, "high": 0.25},
                "calibrated_probabilities": {"low": 0.4, "medium": 0.35, "high": 0.25},
            }
        ),
        "context": low_context,
    }
)
check(route.uncertain is True, "low calibrated confidence should be uncertain")
check(route.selected_model == "cheap", "uncertain route should use the fallback model")

strong = RoutingPolicy().route(
    {"complexity": high_confidence, "reasoning": medium_score, "context": low_context}
)
check(strong.selected_model == "strong", "complex decisions should select the strong model")

soft_reasoning = medium_score.model_copy(
    update={
        "label": "high",
        "calibrated_confidence": 0.39,
        "calibrated_probabilities": {"low": 0.28, "medium": 0.33, "high": 0.39},
    }
)
confident_complex = high_confidence.model_copy(update={"calibrated_confidence": 0.63})
kept = RoutingPolicy().route(
    {
        "complexity": confident_complex,
        "reasoning": soft_reasoning,
        "context": low_context,
    }
)
check(kept.uncertain is False, "a confident complex label should not be discarded")
check(kept.selected_model == "strong", "confident complex queries should use the strong model")

print("DECISION UNIT CHECKS PASSED")
