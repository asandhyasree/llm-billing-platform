import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.anomaly import detect_anomalies


def _make_daily(costs: list[float]) -> list[dict]:
    return [{"date": f"2025-01-{i+1:02d}", "total_cost": c, "model": "gpt-4o"} for i, c in enumerate(costs)]


def test_returns_empty_when_insufficient_data():
    data = _make_daily([1.0, 2.0, 3.0])  # fewer than 7 days
    assert detect_anomalies(data) == []


def test_detects_spike():
    costs = [1.0] * 29 + [50.0]  # one massive spike
    data  = _make_daily(costs)
    anomalies = detect_anomalies(data)
    assert len(anomalies) >= 1
    assert anomalies[0]["total_cost"] == 50.0
    assert anomalies[0]["severity"] in ("medium", "high")


def test_no_false_positives_on_flat_data():
    costs = [1.0] * 30
    data  = _make_daily(costs)
    assert detect_anomalies(data) == []


def test_sorted_by_z_score_descending():
    costs = [1.0] * 27 + [10.0, 20.0, 30.0]
    data  = _make_daily(costs)
    anomalies = detect_anomalies(data)
    z_scores = [abs(a["z_score"]) for a in anomalies]
    assert z_scores == sorted(z_scores, reverse=True)
