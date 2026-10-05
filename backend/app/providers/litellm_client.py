from litellm import completion

from app.providers.config import (
    CHEAP_MODEL,
    STRONG_MODEL,
    NVIDIA_API_KEY,
    NVIDIA_API_BASE,
)


def generate_with_cloud(
    model: str,
    prompt: str,
    history: list[dict] | None = None,
) -> str:

    messages = []

    if history:
        messages.extend(history)

    messages.append(
        {
            "role": "user",
            "content": prompt,
        }
    )

    if model == "cheap":
        cloud_model = CHEAP_MODEL
    elif model == "strong":
        cloud_model = STRONG_MODEL
    else:
        raise ValueError(f"Unknown cloud tier: {model}")

    response = completion(
        model=cloud_model,
        messages=messages,
        api_key=NVIDIA_API_KEY,
        api_base=NVIDIA_API_BASE,
    )

    return response.choices[0].message.content