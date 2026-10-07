"""Configurable demo pricing; replace these placeholder rates with real pricing."""

# Rates are demo placeholders in currency units per one million tokens. They are
# not provider quotes. Keeping the table here makes future pricing updates local.
MODEL_PRICING: dict[str, dict[str, float]] = {
    "local": {"input": 0.0, "output": 0.0},
    "cheap": {"input": 0.15, "output": 0.60},
    "cheap-model": {"input": 0.15, "output": 0.60},
    "strong": {"input": 2.50, "output": 10.00},
    "strong-model": {"input": 2.50, "output": 10.00},
}


def calculate_cost(
    model: str | None, input_tokens: int | None, output_tokens: int | None
) -> float | None:
    """Estimate cost from configurable per-million-token demo rates.

    Returns ``None`` when the model is unconfigured or either token count is
    unavailable. Callers can provide a measured ``estimated_cost`` instead.
    """
    if model is None or input_tokens is None or output_tokens is None:
        return None
    rates = MODEL_PRICING.get(model)
    if rates is None:
        return None
    return (input_tokens * rates["input"] + output_tokens * rates["output"]) / 1_000_000
