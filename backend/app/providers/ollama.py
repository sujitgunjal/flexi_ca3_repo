from litellm import completion

from app.providers.config import (
    OLLAMA_API_BASE,
    OLLAMA_MODEL,
)


def generate_with_ollama(
    prompt: str,
    history: list[dict] | None = None,
    timeout: float | None = None,
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

    options = {}
    if timeout is not None:
        options["timeout"] = timeout

    response = completion(
        model=f"ollama/{OLLAMA_MODEL}",
        messages=messages,
        api_base=OLLAMA_API_BASE,
        **options,
    )

    return response.choices[0].message.content