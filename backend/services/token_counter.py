def extract_usage(response: dict, model: str, provider: str) -> dict:
    """
    Normalize token counts from provider API responses into a single structure.
    Each provider returns usage data in a different shape.
    """
    if provider == "openai":
        u = response.get("usage", {})
        return {
            "input_tokens":  u.get("prompt_tokens", 0),
            "output_tokens": u.get("completion_tokens", 0),
            "model":    model,
            "provider": provider,
        }
    elif provider == "anthropic":
        u = response.get("usage", {})
        return {
            "input_tokens":  u.get("input_tokens", 0),
            "output_tokens": u.get("output_tokens", 0),
            "model":    model,
            "provider": provider,
        }
    elif provider == "gemini":
        u = response.get("usageMetadata", {})
        return {
            "input_tokens":  u.get("promptTokenCount", 0),
            "output_tokens": u.get("candidatesTokenCount", 0),
            "model":    model,
            "provider": provider,
        }
    else:
        raise ValueError(f"Unknown provider: {provider}")
