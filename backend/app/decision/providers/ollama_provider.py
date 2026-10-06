import json
import os
import urllib.error
import urllib.request

from app.decision.base import DecisionProviderError
from app.providers.config import OLLAMA_API_BASE, OLLAMA_MODEL


SYSTEM_PROMPT = """You are a query classifier for an LLM router.
Do not answer the user's question.
Do not explain your reasoning.
Return only a JSON object with probability distributions for three decisions.

Use exactly these keys and class names:
{
  "complexity": {"simple": 0.0, "medium": 0.0, "complex": 0.0},
  "reasoning": {"low": 0.0, "medium": 0.0, "high": 0.0},
  "context": {"low": 0.0, "medium": 0.0, "high": 0.0}
}

Rules:
- complexity: simple, medium, or complex
- reasoning: how much multi-step reasoning is required (low, medium, high)
- context: how much surrounding context is required (low, medium, high)
- Every probability is a number from 0 to 1
- The three probabilities in each decision sum to 1
- Do not set every class in a decision to 0
- Put the highest probability on the class you believe is correct

Example for "What is 2 + 2?":
{
  "complexity": {"simple": 0.9, "medium": 0.1, "complex": 0.0},
  "reasoning": {"low": 0.85, "medium": 0.15, "high": 0.0},
  "context": {"low": 0.9, "medium": 0.1, "high": 0.0}
}
"""


class OllamaDecisionProvider:
    """Permanent local decision provider. This is the default Jev-inspired engine."""

    name = "ollama"

    def __init__(self, model: str | None = None, api_base: str | None = None):
        self.model_name = model or os.getenv("DECISION_OLLAMA_MODEL", OLLAMA_MODEL)
        self.api_base = (api_base or OLLAMA_API_BASE).rstrip("/")

    def classify_raw(self, query: str, *, correction: str | None = None) -> str:
        user_content = f"Classify this query:\n{query.strip()}"
        if correction:
            user_content = f"{correction}\n\n{user_content}"

        body = {
            "model": self.model_name,
            "stream": False,
            "format": "json",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            "options": {
                "temperature": 0,
                "num_predict": 400,
            },
        }
        request = urllib.request.Request(
            f"{self.api_base}/api/chat",
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise DecisionProviderError(
                f"Local Ollama decision model is unavailable at {self.api_base}"
            ) from exc
        except TimeoutError as exc:
            raise DecisionProviderError(
                "Local Ollama decision model timed out"
            ) from exc
        except json.JSONDecodeError as exc:
            raise DecisionProviderError(
                "Local Ollama decision model returned invalid JSON"
            ) from exc

        message = payload.get("message", {})
        content = message.get("content") if isinstance(message, dict) else None
        if not isinstance(content, str) or not content.strip():
            raise DecisionProviderError(
                "Local Ollama decision model returned an empty classification"
            )

        return content
