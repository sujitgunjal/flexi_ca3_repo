def count_tokens(text: str) -> int:
    """Approximate tokens as one token per four characters.

    The same counter is used before and after selection, so the reduction
    percentage stays comparable even without a model-specific tokenizer.
    """

    if not text or not text.strip():
        return 0
    return max(1, (len(text) + 3) // 4)
