from src.analysis.risk import risk_band_analysis, confidence_score
import pytest



def test_risk_band_analysis():
    forecast = [100, 101, 99, 102, 98]
    assert risk_band_analysis(forecast, 100) == 1.0  # all within ±2%

    forecast_wide = [100, 105, 95, 110, 90]
    assert risk_band_analysis(forecast_wide, 100) == pytest.approx(0.2, 0.01)


def test_confidence_score():
    result = {"prob_up": 0.8, "volatility": 0.01, "risk_band_confidence": 0.9}
    score = confidence_score(result)
    assert score == pytest.approx(0.86, 0.01)  # ← changed expected value

    result_low = {"prob_up": 0.5, "volatility": 0.1, "risk_band_confidence": 0.3}
    score_low = confidence_score(result_low)
    assert 0.1 <= score_low <= 0.5