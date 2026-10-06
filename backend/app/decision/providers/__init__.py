import os

from app.decision.base import DecisionProvider, DecisionProviderError
from app.decision.providers.jev_provider import JevDecisionProvider
from app.decision.providers.ollama_provider import OllamaDecisionProvider


def get_decision_provider(name: str | None = None) -> DecisionProvider:
    selected = (name or os.getenv("DECISION_PROVIDER", "ollama")).strip().lower()

    if selected in {"", "ollama", "local"}:
        return OllamaDecisionProvider()

    if selected == "jev":
        return JevDecisionProvider()

    raise DecisionProviderError(
        f"Unknown decision provider '{selected}'. Use 'ollama' or the optional 'jev'."
    )
