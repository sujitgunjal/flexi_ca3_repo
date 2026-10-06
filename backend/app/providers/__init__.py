from app.providers.litellm_client import generate_with_cloud
from app.providers.ollama import generate_with_ollama
from app.providers.registry import get_tier


def generate_response(
    model: str,
    prompt: str,
    history: list[dict] | None = None,
    timeout: float | None = None,
) -> str:
    """Generate a reply for a tier name: local, cheap, or strong."""

    tier = get_tier(model)

    if tier.provider == "ollama":
        return generate_with_ollama(
            prompt,
            history,
            timeout=timeout,
        )

    return generate_with_cloud(
        model,
        prompt,
        history,
        timeout=timeout,
    )