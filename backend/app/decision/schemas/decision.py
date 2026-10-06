from pydantic import BaseModel, Field


COMPLEXITY_CLASSES = ("simple", "medium", "complex")
REASONING_CLASSES = ("low", "medium", "high")
CONTEXT_CLASSES = ("low", "medium", "high")

TASKS: dict[str, tuple[str, ...]] = {
    "complexity": COMPLEXITY_CLASSES,
    "reasoning": REASONING_CLASSES,
    "context": CONTEXT_CLASSES,
}


class DecisionScore(BaseModel):
    label: str
    raw_probabilities: dict[str, float]
    raw_confidence: float = Field(ge=0, le=1)
    calibrated_probabilities: dict[str, float]
    calibrated_confidence: float = Field(ge=0, le=1)


class DecisionResponse(BaseModel):
    request_id: str
    query: str
    provider: str
    decision_model: str
    output_valid: bool
    calibration_applied: bool
    complexity: DecisionScore
    reasoning: DecisionScore
    context: DecisionScore
    uncertain: bool
    fallback_used: bool
    selected_model: str
    routing_reason: str
