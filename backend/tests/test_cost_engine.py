import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.cost_engine import calculate_cost


def test_gpt4o_cost():
    usage = {"model": "gpt-4o", "input_tokens": 1_000_000, "output_tokens": 1_000_000}
    costs = calculate_cost(usage, markup_pct=0)
    assert costs["input_cost"]  == 2.50
    assert costs["output_cost"] == 10.00
    assert costs["total_cost"]  == 12.50
    assert costs["billed_cost"] == 12.50


def test_markup_applied():
    usage = {"model": "gpt-4o-mini", "input_tokens": 1_000_000, "output_tokens": 0}
    costs = calculate_cost(usage, markup_pct=20)
    assert costs["billed_cost"] == pytest.approx(0.15 * 1.20, rel=1e-6)


def test_unknown_model_uses_fallback():
    usage = {"model": "unknown-model-xyz", "input_tokens": 1_000_000, "output_tokens": 0}
    costs = calculate_cost(usage)
    assert costs["input_cost"] == pytest.approx(0.001, rel=1e-6)


def test_zero_tokens():
    usage = {"model": "gpt-4o", "input_tokens": 0, "output_tokens": 0}
    costs = calculate_cost(usage)
    assert costs["total_cost"] == 0.0
    assert costs["billed_cost"] == 0.0
