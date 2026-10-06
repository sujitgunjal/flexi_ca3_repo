from typing import Any, TypedDict


class RequestState(TypedDict, total=False):
    query: str
    conversation_history: list[dict[str, Any]]

    complexity: str
    reasoning: str
    context_requirement: str
    optimized_context: str
    selected_model: str
    routing_reason: str
    uncertain: bool
    decision: dict[str, Any]

    cache_hit: bool

    quality_score: float
    escalation: bool

    cost: float
    latency: float

    response: str