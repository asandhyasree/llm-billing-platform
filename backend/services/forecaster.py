from datetime import date


def _linear_regression(x: list[float], y: list[float]) -> tuple[float, float]:
    n   = len(x)
    sx  = sum(x)
    sy  = sum(y)
    sxy = sum(xi * yi for xi, yi in zip(x, y))
    sxx = sum(xi ** 2 for xi in x)
    denom = n * sxx - sx ** 2
    if denom == 0:
        return 0.0, sum(y) / n if y else 0.0
    slope     = (n * sxy - sx * sy) / denom
    intercept = (sy - slope * sx) / n
    return slope, intercept


def forecast_month_end(daily_costs: list[float]) -> dict:
    """
    Project month-end spend using linear regression on the provided daily costs.

    Args:
        daily_costs: ordered list of daily spend values (most recent last).

    Returns:
        Dict with spend_so_far, projected_remaining, projected_month_total, trend, etc.
    """
    today          = date.today()
    days_elapsed   = today.day
    days_in_month  = 30  # simplified constant

    x = list(range(len(daily_costs)))
    slope, intercept = _linear_regression(x, daily_costs)

    days_remaining = max(0, days_in_month - days_elapsed)
    future_x  = [len(daily_costs) + i for i in range(days_remaining)]
    projected = [max(0.0, slope * d + intercept) for d in future_x]

    spent    = sum(daily_costs)
    forecast = sum(projected)

    if slope > 0.001:
        trend = "increasing"
    elif slope < -0.001:
        trend = "decreasing"
    else:
        trend = "stable"

    return {
        "spent_so_far_usd":          round(spent,           4),
        "projected_remaining_usd":   round(forecast,        4),
        "projected_month_total_usd": round(spent + forecast, 4),
        "trend":                     trend,
        "slope_usd_per_day":         round(slope,            6),
        "days_of_data":              len(daily_costs),
        "days_projected":            days_remaining,
    }
