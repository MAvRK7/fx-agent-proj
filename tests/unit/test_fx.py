import pytest
from unittest.mock import patch
from src.analysis.fx import analyze_fx


@patch("src.analysis.fx.risk_band_analysis")
@patch("src.analysis.fx.monte_carlo_simulation")
@patch("src.analysis.fx.get_current_rate")
@patch("src.analysis.fx.get_historical_rates")
def test_analyze_fx_strong_uptrend(mock_hist, mock_current, mock_mc, mock_risk):
    # True steady uptrend (no resets)
    mock_hist.return_value = list(range(80, 130))  # 50 days clean rising
    mock_current.return_value = 85.0

    # Force bullish Monte Carlo
    mock_mc.return_value = [90.0] * 100

    # High confidence
    mock_risk.return_value = 0.9

    result = analyze_fx()

    assert result["current_rate"] == pytest.approx(85.0, abs=0.01)
    assert result["prob_up"] > 0.70
    assert "wait" in result["decision"].lower()
    assert result["confidence"] > 0.70
    assert "low volatility" in result["risk"].lower()
    assert "expected_7d" in result


@patch("src.analysis.fx.risk_band_analysis")
@patch("src.analysis.fx.monte_carlo_simulation")
@patch("src.analysis.fx.get_current_rate")
@patch("src.analysis.fx.get_historical_rates")
def test_analyze_fx_high_volatility_low_confidence(mock_hist, mock_current, mock_mc, mock_risk):
    choppy = [100, 110, 90, 115, 85, 120, 80, 125, 75, 130] * 5
    mock_hist.return_value = choppy
    mock_current.return_value = 100.0

    # Mixed outcomes
    mock_mc.return_value = [80, 120] * 50

    # Low confidence
    mock_risk.return_value = 0.4

    result = analyze_fx()

    assert result["volatility"] > 0.03
    assert result["confidence"] < 0.55
    assert "high volatility" in result["risk"].lower()


@patch("src.analysis.fx.get_current_rate")
@patch("src.analysis.fx.get_historical_rates")
def test_analyze_fx_insufficient_history_raises_error(mock_hist, mock_current):
    mock_current.return_value = 85.0
    mock_hist.return_value = [85.0] * 1

    with pytest.raises(Exception):
        analyze_fx()


@patch("src.analysis.fx.risk_band_analysis")
@patch("src.analysis.fx.monte_carlo_simulation")
@patch("src.analysis.fx.get_current_rate")
@patch("src.analysis.fx.get_historical_rates")
def test_analyze_fx_custom_amount_scenario(mock_hist, mock_current, mock_mc, mock_risk):
    mock_hist.return_value = list(range(80, 120))
    mock_current.return_value = 85.0
    mock_mc.return_value = [90.0] * 100
    mock_risk.return_value = 0.8

    result = analyze_fx()

    assert "scenario" in result
    assert "difference" in result["scenario"]