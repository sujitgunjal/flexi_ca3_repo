import json
import os
import urllib.error
import urllib.request

from app.decision.base import DecisionProviderError


class JevDecisionProvider:
    """Optional future paid TypeSafe Jev provider.

    The local Ollama provider remains the default. This class is used only when
    DECISION_PROVIDER=jev and both JEV_API_KEY and JEV_API_BASE are set.
    """

    name = "jev"
    model_name = "jev"

    def __init__(
        self,
        api_key: str | None = None,
        api_base: str | None = None,
    ):
        self.api_key = api_key if api_key is not None else os.getenv("JEV_API_KEY", "")
        self.api_base = (
            api_base if api_base is not None else os.getenv("JEV_API_BASE", "")
        ).rstrip("/")

    def classify_raw(self, query: str, *, correction: str | None = None) -> str:
        if not self.api_key or not self.api_base:
            raise DecisionProviderError(
                "TypeSafe Jev is an optional paid provider and is not configured. "
                "Use the local Ollama decision provider, which is the project default."
            )

        prompt = query.strip()
        if correction:
            prompt = f"{correction}\n\n{prompt}"

        body = json.dumps({"query": prompt}).encode("utf-8")
        request = urllib.request.Request(
            self.api_base,
            data=body,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raise DecisionProviderError(
                f"Optional Jev provider returned HTTP {exc.code}"
            ) from exc
        except urllib.error.URLError as exc:
            raise DecisionProviderError("Optional Jev provider is unavailable") from exc
        except TimeoutError as exc:
            raise DecisionProviderError("Optional Jev provider timed out") from exc
        except json.JSONDecodeError as exc:
            raise DecisionProviderError(
                "Optional Jev provider returned invalid JSON"
            ) from exc

        if isinstance(payload, dict) and isinstance(payload.get("content"), str):
            return payload["content"]

        return json.dumps(payload)
