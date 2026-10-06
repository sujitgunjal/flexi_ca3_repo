from typing import Protocol


class DecisionProviderError(RuntimeError):
    """The decision provider could not be reached or was not configured."""


class DecisionProvider(Protocol):
    name: str
    model_name: str

    def classify_raw(self, query: str, *, correction: str | None = None) -> str:
        """Return the provider's raw classifier output. Do not answer the query."""
