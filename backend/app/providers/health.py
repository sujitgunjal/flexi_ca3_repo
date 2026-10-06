import json
import socket
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass

from app.providers.config import NVIDIA_API_KEY, PROVIDER_TIMEOUT_SECONDS
from app.providers.registry import ModelTier, get_tier, list_tiers


@dataclass
class ProviderHealth:
    tier: str
    provider: str
    model: str
    available: bool
    status: str
    detail: str
    latency_ms: float

    def as_dict(self) -> dict:
        return asdict(self)


def check_provider(tier: str) -> ProviderHealth:
    spec = get_tier(tier)
    started = time.perf_counter()

    try:
        if spec.provider == "ollama":
            return _check_ollama(spec, started)

        return _check_nvidia(spec, started)
    except Exception:
        return _result(
            spec,
            started,
            available=False,
            status="error",
            detail="API error",
        )


def check_all_providers() -> list[ProviderHealth]:
    tiers = [item.tier for item in list_tiers()]

    with ThreadPoolExecutor(max_workers=len(tiers)) as pool:
        return list(pool.map(check_provider, tiers))


def _check_ollama(spec: ModelTier, started: float) -> ProviderHealth:
    url = f"{spec.api_base.rstrip('/')}/api/tags"
    payload, failure = _get_json(url, timeout=PROVIDER_TIMEOUT_SECONDS)

    if failure is not None:
        status, detail = failure
        return _result(spec, started, available=False, status=status, detail=detail)

    names = [
        item.get("name", "")
        for item in payload.get("models", [])
        if isinstance(item, dict)
    ]

    if not _model_listed(spec.model, names):
        return _result(
            spec,
            started,
            available=False,
            status="unavailable",
            detail=f"Model '{spec.model}' is not installed in Ollama",
        )

    return _result(
        spec,
        started,
        available=True,
        status="healthy",
        detail="Ollama is responding and the model is installed",
    )


def _check_nvidia(spec: ModelTier, started: float) -> ProviderHealth:
    if not NVIDIA_API_KEY:
        return _result(
            spec,
            started,
            available=False,
            status="error",
            detail="NVIDIA API key is not configured",
        )

    url = f"{spec.api_base.rstrip('/')}/models"
    payload, failure = _get_json(
        url,
        timeout=PROVIDER_TIMEOUT_SECONDS,
        headers={
            "Authorization": f"Bearer {NVIDIA_API_KEY}",
            "Accept": "application/json",
        },
    )

    if failure is not None:
        status, detail = failure
        return _result(spec, started, available=False, status=status, detail=detail)

    catalog = payload.get("data")
    if not isinstance(catalog, list):
        return _result(
            spec,
            started,
            available=False,
            status="error",
            detail="API error: unexpected response",
        )

    names = [
        item.get("id", "")
        for item in catalog
        if isinstance(item, dict)
    ]

    if not _model_listed(spec.model, names):
        return _result(
            spec,
            started,
            available=False,
            status="unavailable",
            detail=f"Model '{spec.model}' is not available from the provider",
        )

    return _result(
        spec,
        started,
        available=True,
        status="healthy",
        detail="Cloud provider is responding and the model is available",
    )


def _model_listed(configured: str, available: list[str]) -> bool:
    wanted = _model_aliases(configured)

    for name in available:
        if _model_aliases(name) & wanted:
            return True

    return False


def _model_aliases(name: str) -> set[str]:
    cleaned = name.strip()
    aliases = {cleaned}

    if "/" in cleaned:
        aliases.add(cleaned.split("/", 1)[1])

    if ":" in cleaned:
        aliases.add(cleaned.split(":", 1)[0])

    return {alias for alias in aliases if alias}


def _get_json(
    url: str,
    timeout: float,
    headers: dict[str, str] | None = None,
) -> tuple[dict | None, tuple[str, str] | None]:
    request = urllib.request.Request(url, headers=headers or {})

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        return None, ("error", f"API error: HTTP {exc.code}")
    except (TimeoutError, socket.timeout):
        return None, ("timeout", "Provider timed out")
    except urllib.error.URLError as exc:
        reason = exc.reason
        if isinstance(reason, (TimeoutError, socket.timeout)):
            return None, ("timeout", "Provider timed out")
        return None, ("connection_error", "Connection failed")
    except Exception:
        return None, ("error", "API error")

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return None, ("error", "API error: response was not valid JSON")

    if not isinstance(payload, dict):
        return None, ("error", "API error: unexpected response")

    return payload, None


def _result(
    spec: ModelTier,
    started: float,
    available: bool,
    status: str,
    detail: str,
) -> ProviderHealth:
    elapsed_ms = (time.perf_counter() - started) * 1000

    return ProviderHealth(
        tier=spec.tier,
        provider=spec.provider,
        model=spec.model,
        available=available,
        status=status,
        detail=detail,
        latency_ms=round(elapsed_ms, 1),
    )
