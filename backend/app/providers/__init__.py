from app.providers.litellm_client import generate_with_cloud
from app.providers.ollama import generate_with_ollama


def generate_response(
    model: str,
    prompt: str,
    history: list[dict] | None = None,
) -> str:

    if model == "local":
        return generate_with_ollama(
            prompt,
            history,
        )

    if model in {"cheap", "strong"}:
        return generate_with_cloud(
            model,
            prompt,
            history,
        )

    raise ValueError(
        f"Unknown model tier: {model}"
    )