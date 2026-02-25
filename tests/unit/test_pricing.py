
from src.utils.pricing import estimate_model_cost
import pytest

def test_estimate_model_cost():
    # Small tokens → rounds to 0 (correct behavior)
    cost_small = estimate_model_cost("stepfun/step-3.5-flash:free", 1000, 500)
    assert cost_small == pytest.approx(0.00025, abs=1e-6)

    # Large example (realistic prompt + response)
    cost_large = estimate_model_cost("stepfun/step-3.5-flash:free", 1_000_000, 500_000)
    # 1M input × 0.10/M = 0.10
    # 0.5M output × 0.30/M = 0.15
    # total = 0.25
    assert cost_large == pytest.approx(0.250000, abs=0.000001)

    # Fallback model
    cost_fallback = estimate_model_cost("unknown", 1_000_000, 500_000)
    assert cost_fallback == pytest.approx(0.250000, abs=0.000001)