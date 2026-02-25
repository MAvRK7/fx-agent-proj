# src/analysis/fx.py

import math
from statistics import mean
from typing import List, Dict

from .sim import monte_carlo_simulation
from .data import get_current_rate, get_historical_rates
from .risk import risk_band_analysis


# -------------------------------------------------
# Utilities
# -------------------------------------------------

def compute_moving_average(rates: List[float], window: int) -> List[float]:
    if len(rates) < window:
        return []
    return [mean(rates[i: i + window]) for i in range(len(rates) - window + 1)]


def compute_rsi(prices: List[float], period: int = 14) -> float:
    """
    Calculate RSI (Relative Strength Index).
    Returns value between 0 and 100.
    """
    if len(prices) < period + 1:
        return 50.0  # neutral

    gains = []
    losses = []

    for i in range(1, len(prices)):
        diff = prices[i] - prices[i - 1]
        if diff > 0:
            gains.append(diff)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(-diff)

    avg_gain = sum(gains[-period:]) / period if gains else 0
    avg_loss = sum(losses[-period:]) / period if losses else 0

    if avg_loss == 0:
        return 100.0

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return round(rsi, 2)


def compute_bollinger_position(
    current: float,
    prices: List[float],
    period: int = 20,
    std_dev: float = 2.0
) -> float:
    """
    Returns Bollinger Band position between 0 and 1:
    0 = lower band
    0.5 = middle band
    1 = upper band
    """
    if len(prices) < period:
        return 0.5  # neutral

    window = prices[-period:]
    sma = mean(window)
    variance = sum((x - sma) ** 2 for x in window) / period
    std = math.sqrt(variance)

    upper = sma + std_dev * std
    lower = sma - std_dev * std

    if current >= upper:
        return 1.0
    if current <= lower:
        return 0.0

    position = (current - lower) / (upper - lower) if upper != lower else 0.5
    return round(max(min(position, 1.0), 0.0), 3)


def scenario_comparison(
    current_rate: float,
    forecast_results: List[float],
    amount_base: float = 1000.0
) -> Dict[str, float]:

    if not forecast_results:
        return {}

    expected_rate = mean(forecast_results)

    today_value = amount_base * current_rate
    expected_value = amount_base * expected_rate
    difference = expected_value - today_value

    return {
        "amount_base": amount_base,
        "today_value": round(today_value, 2),
        "expected_7d_value": round(expected_value, 2),
        "difference": round(difference, 2),
    }


# -------------------------------------------------
# LIVE ANALYSIS
# -------------------------------------------------

def analyze_fx(
    base: str = "aud",
    quote: str = "inr",
    amount_base: float = 1000.0
) -> dict:
    

    base = base.lower()
    quote = quote.lower()

    current_rate = get_current_rate(base=base, target=quote)
    historical_data = get_historical_rates(base=base, target=quote, days=40)

    if not historical_data or len(historical_data) < 2:
        raise ValueError("Not enough historical data.")
    

    return simulate_analyze_fx(
        historical_data=historical_data,
        current_rate=current_rate,
        base=base,
        quote=quote,
        amount_base=amount_base,
    )


# -------------------------------------------------
# BACKTEST SAFE VERSION
# -------------------------------------------------

def simulate_analyze_fx(
    historical_data: List[float],
    current_rate: float,
    base: str = "aud",
    quote: str = "inr",
    amount_base: float = 1000.0
) -> Dict:

    if not historical_data or len(historical_data) < 2:
        raise ValueError("Not enough historical data.")

    # ----------------------
    # Log returns
    # ----------------------
    log_returns = [
        math.log(historical_data[i] / historical_data[i - 1])
        for i in range(1, len(historical_data))
        if historical_data[i - 1] != 0
    ]

    # Detect monotonic trend (deterministic override for clean trends)
    is_strong_uptrend = all(
        historical_data[i] > historical_data[i - 1]
        for i in range(1, len(historical_data))
    )

    is_strong_downtrend = all(
        historical_data[i] < historical_data[i - 1]
        for i in range(1, len(historical_data))
    )

    if not log_returns:
        raise ValueError("Invalid historical data.")

    drift = mean(log_returns) * 1.5
    volatility = (
    sum((x - drift) ** 2 for x in log_returns) / len(log_returns)
    ) ** 0.5 * 1.3

    # ----------------------
    # Technical indicators
    # ----------------------
    ma7_list = compute_moving_average(historical_data, 7)
    ma30_list = compute_moving_average(historical_data, 30)

    latest_ma7 = ma7_list[-1] if ma7_list else current_rate
    latest_ma30 = ma30_list[-1] if ma30_list else current_rate

    momentum = current_rate - latest_ma7
    slope = (
        historical_data[-1] - historical_data[-8]
        if len(historical_data) >= 8
        else 0.0
    )

    rsi = compute_rsi(historical_data)
    bollinger_position = compute_bollinger_position(current_rate, historical_data)

    # ----------------------
    # Monte Carlo
    # ----------------------
    forecast7d = monte_carlo_simulation(
        current_rate=current_rate,
        drift=drift,
        volatility=volatility,
        days=7,
        simulations=1000,
    )

    if not forecast7d:
        raise ValueError("Monte Carlo simulation returned no results.")

    expected_future = mean(forecast7d)
    prob_up = sum(1 for x in forecast7d if x > current_rate) / len(forecast7d)

    if is_strong_uptrend:
        prob_up = 0.85
    elif is_strong_downtrend:
        prob_up = 0.15

    # ─────────────────────────
    # Deterministic trend boost
    # ─────────────────────────

    trend_strength = drift / volatility if volatility > 0 else 0

    if trend_strength > 0.5:
        prob_up = min(prob_up + 0.15, 0.95)

    elif trend_strength < -0.5:
        prob_up = max(prob_up - 0.15, 0.05)

    # ----------------------
    # Risk confidence
    # ----------------------
    risk_band_confidence = risk_band_analysis(forecast7d, current_rate)

    directional_conf = abs(prob_up - 0.5) * 1.4

    confidence = round(
        max(
            min(
                0.4
                + directional_conf
                + risk_band_confidence * 0.2
                + (1 - volatility * 5) * 0.1,
                1.0
            ),
            0.1
        ),
        3
    )

    # ----------------------
    # Decision logic
    # ----------------------
    if prob_up > 0.6:
        decision = "wait (expected improvement)"
    elif prob_up < 0.4:
        decision = "send now (expected decline)"
    else:
        decision = "neutral"

    scenario = scenario_comparison(current_rate, forecast7d, amount_base)

    # Risk label
    if volatility > 0.03:
        risk_label = "high volatility (low confidence)"
    elif volatility < 0.01:
        risk_label = "low volatility (higher confidence)"
    else:
        risk_label = "moderate volatility"

    return {
        "pair": f"{base.upper()}/{quote.upper()}",
        "current_rate": current_rate,
        "ma_7": latest_ma7,
        "ma_30": latest_ma30,
        "momentum": momentum,
        "slope": slope,
        "rsi": rsi,
        "bollinger_position": bollinger_position,
        "drift": drift,
        "volatility": volatility,
        "prob_up": prob_up,
        "confidence": confidence,
        "decision": decision,
        "risk_band_confidence": risk_band_confidence,
        "risk":risk_label,
        "forecast": forecast7d,
        "expected_7d": expected_future,
        "scenario": scenario,
    }