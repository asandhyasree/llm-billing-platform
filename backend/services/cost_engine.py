from config import MODEL_RATES

_FALLBACK_RATES = {"input": 0.001, "output": 0.003}


def calculate_cost(usage: dict, markup_pct: float = 20.0) -> dict:
    """
    Convert token counts into USD costs, then apply the tenant markup.

    Returns a dict with input_cost, output_cost, total_cost, and billed_cost (after markup).
    Cost is stored at event time — not invoice time — to preserve historical accuracy
    even when provider pricing changes.
    """
    model = usage["model"]
    rates = MODEL_RATES.get(model, _FALLBACK_RATES)

    input_cost  = (usage["input_tokens"]  / 1_000_000) * rates["input"]
    output_cost = (usage["output_tokens"] / 1_000_000) * rates["output"]
    total_cost  = input_cost + output_cost
    billed_cost = total_cost * (1 + markup_pct / 100)

    return {
        "input_cost":   round(input_cost,  8),
        "output_cost":  round(output_cost, 8),
        "total_cost":   round(total_cost,  8),
        "billed_cost":  round(billed_cost, 8),
    }
