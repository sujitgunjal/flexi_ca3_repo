from dataclasses import dataclass

from app.providers.config import (
    CHEAP_MODEL,
    NVIDIA_API_BASE,
    OLLAMA_API_BASE,
    OLLAMA_MODEL,
    STRONG_MODEL,
)


@dataclass(frozen=True)
class ModelTier:
    tier: str
    provider: str
    model: str
    api_base: str


def list_tiers() -> list[ModelTier]:
    return [
        ModelTier(
            tier="local",
            provider="ollama",
            model=OLLAMA_MODEL,
            api_base=OLLAMA_API_BASE,
        ),
        ModelTier(
            tier="cheap",
            provider="nvidia",
            model=CHEAP_MODEL,
            api_base=NVIDIA_API_BASE,
        ),
        ModelTier(
            tier="strong",
            provider="nvidia",
            model=STRONG_MODEL,
            api_base=NVIDIA_API_BASE,
        ),
    ]


def get_tier(tier: str) -> ModelTier:
    for item in list_tiers():
        if item.tier == tier:
            return item

    raise ValueError(f"Unknown model tier: {tier}")
