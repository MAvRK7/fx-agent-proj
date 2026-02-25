# src/analysis/__init__.py
# This file can be left empty, or you can expose the most important functions:

from .fx import analyze_fx
from .data import get_current_rate, get_historical_rates
from .risk import risk_band_analysis, confidence_score
from .sim import monte_carlo_simulation

__all__ = [
    "analyze_fx",
    "get_current_rate",
    "get_historical_rates",
    "risk_band_analysis",
    "confidence_score",
    "monte_carlo_simulation",
]