import math

from app.providers.config import CONTEXT_MESSAGE_CAPS, CONTEXT_TOKEN_LIMITS
from app.services.token_service import count_tokens


def context_budget(requirement: str | None) -> tuple[int, int]:
    level = requirement if requirement in CONTEXT_TOKEN_LIMITS else "medium"
    return CONTEXT_TOKEN_LIMITS[level], CONTEXT_MESSAGE_CAPS[level]


def select_relevant_messages(
    query: str,
    history: list[dict],
    embeddings: list[list[float]],
    token_limit: int,
    message_cap: int,
) -> list[dict]:
    """Rank history by similarity to the query and keep messages inside the budget.

    Selected messages are returned in their original conversation order.
    """

    if not history or token_limit <= 0 or message_cap <= 0:
        return []

    query_vector = embeddings[0]
    ranked = []
    for index, message in enumerate(history):
        ranked.append(
            (
                _cosine(query_vector, embeddings[index + 1]),
                index,
                message,
            )
        )
    ranked.sort(key=lambda item: item[0], reverse=True)

    chosen: list[tuple[float, int, dict]] = []
    used_tokens = 0
    for score, index, message in ranked:
        if len(chosen) >= message_cap:
            break
        cost = count_tokens(str(message.get("content", "")))
        if cost == 0 or used_tokens + cost > token_limit:
            continue
        chosen.append((score, index, message))
        used_tokens += cost

    chosen.sort(key=lambda item: item[1])
    return [
        {
            "role": str(message.get("role", "user")),
            "content": str(message.get("content", "")),
            "similarity": round(score, 4),
        }
        for score, _index, message in chosen
    ]


def render_context(query: str, messages: list[dict]) -> str:
    lines = [
        f"{message['role']}: {message['content']}"
        for message in messages
    ]
    lines.append(f"user: {query}")
    return "\n".join(lines)


def _cosine(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)
