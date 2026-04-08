import statistics


def detect_anomalies(daily_usage: list[dict], z_threshold: float = 2.0) -> list[dict]:
    """
    Flag days where a tenant's spend is statistically unusual using a rolling z-score.

    Args:
        daily_usage: list of dicts with at least {"date": str, "total_cost": float}
        z_threshold: number of standard deviations to consider anomalous

    Returns:
        Anomalous days sorted by z-score magnitude (most extreme first).
        Returns empty list if fewer than 7 days of history exist.
    """
    if len(daily_usage) < 7:
        return []

    costs = [d["total_cost"] for d in daily_usage]
    mean  = statistics.mean(costs)
    stdev = statistics.stdev(costs) if len(costs) > 1 else 1.0

    if stdev == 0:
        return []

    anomalies = []
    for day in daily_usage:
        z = (day["total_cost"] - mean) / stdev
        if abs(z) > z_threshold:
            anomalies.append({
                **day,
                "z_score":       round(z, 2),
                "mean_cost":     round(mean, 6),
                "severity":      "high" if abs(z) > 3 else "medium",
                "deviation_pct": round((day["total_cost"] - mean) / mean * 100, 1),
            })

    return sorted(anomalies, key=lambda x: abs(x["z_score"]), reverse=True)
