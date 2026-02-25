# src/analysis/risk.py
from typing import Dict, List


def risk_band_analysis(forecast: List[float], current_rate: float, band_pct: float = 0.02) -> float:
    """
    Calculate the proportion of the forecast that falls within ±band_pct of the current rate.
    Higher value = more stable / predictable short-term movement.
    """
    lower_band = current_rate * (1 - band_pct)
    upper_band = current_rate * (1 + band_pct)
    within_band = sum(lower_band <= x <= upper_band for x in forecast) / len(forecast)
    return round(within_band, 3)


def confidence_score(result: Dict) -> float:
    """
    Compute a 0–1 confidence score based on:
    - Strength of directional probability
    - Volatility penalty
    Uses keys from analyze_fx() result.
    """
    prob_strength = abs(result["prob_up"] - 0.5) * 2          # 0.0 to 1.0
    volatility_penalty = min(result["volatility"] / 0.02, 1.0)  # normalize

    # Optional: use risk_band if available
    risk_factor = result.get("risk_band_confidence", 0.5)

    score = 0.5 + (prob_strength * 0.35) + (risk_factor * 0.25) - (volatility_penalty * 0.15)
    return round(max(min(score, 1.0), 0.1), 3)