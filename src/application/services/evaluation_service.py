# src/application/services/evaluation_service.py
"""
Historical backtest for FX model using the full ensemble.
"""

import math
from datetime import datetime
from statistics import mean
from typing import Dict, Any

from src.analysis.data import load_cache
from src.analysis.sim import monte_carlo_simulation
from src.analysis.fx import compute_rsi, compute_bollinger_position


def run_backtest(interval: int = 2) -> Dict[str, Any]:
    """
    Backtest the model on historical data using the full ensemble.
    """

    try:
        cache = load_cache()

        date_keys = sorted([
            k for k in cache
            if k.endswith("_inr_aud") or k.endswith("_aud_inr")
        ])

        if len(date_keys) < 48:
            return {
                "message": f"Not enough historical data ({len(date_keys)} days). Need ≥48."
            }

        dates = [datetime.strptime(k.split("_")[0], "%Y-%m-%d").date() for k in date_keys]

        rate_map = {}
        for k in date_keys:
            d = datetime.strptime(k.split("_")[0], "%Y-%m-%d").date()
            rate_map[d] = cache[k]

        results = []

        for i in range(40, len(dates) - 7, interval):

            hist_dates = dates[max(0, i - 40): i + 1]
            hist = [rate_map.get(d) for d in hist_dates if d in rate_map]

            if len(hist) < 40:
                continue

            current = hist[-1]
            pred_date = dates[i]

            # ── Full feature calculation ────────────────────────────────────────────
            log_returns = []
            for j in range(1, len(hist)):
                if hist[j - 1] == 0:
                    continue
                log_returns.append(math.log(hist[j] / hist[j - 1]))

            if not log_returns:
                continue

            drift = mean(log_returns)
            vol = (sum((x - drift) ** 2 for x in log_returns) / len(log_returns)) ** 0.5 or 0.01

            ma7 = mean(hist[-7:]) if len(hist) >= 7 else current
            ma30 = mean(hist[-30:]) if len(hist) >= 30 else current

            momentum = current - ma7
            slope = hist[-1] - hist[-8] if len(hist) >= 8 else 0.0

            # Monte Carlo
            fcst = monte_carlo_simulation(current, drift, vol, days=7, simulations=500)
            if not fcst:
                continue

            prob_mc = sum(1 for x in fcst if x > current) / len(fcst)

            # Mean reversion
            mr = 0.5
            if current > ma30 * 1.01:
                mr = 0.2
            elif current < ma30 * 0.99:
                mr = 0.8

            # Momentum
            mom = 0.5 + (momentum / vol * 0.3) if vol > 0 else 0.5

            # Trend
            tr = 0.5 + (slope / vol * 0.2) if vol > 0 else 0.5

            # RSI
            rsi = compute_rsi(hist)
            if rsi > 70:
                rsi_prob = 0.25
            elif rsi < 30:
                rsi_prob = 0.75
            else:
                rsi_prob = 0.5

            # Bollinger
            bb = compute_bollinger_position(current, hist)
            bb_prob = 1 - bb  # lower band = oversold = higher probability up

            # Ensemble (original weights)
            prob = (
                0.20 * prob_mc +
                0.25 * mr +
                0.15 * mom +
                0.15 * tr +
                0.15 * rsi_prob +
                0.10 * bb_prob
            )

            pred_dir = "up" if prob > 0.5 else "down"

            ps = abs(prob - 0.5) * 2
            conf = round(
                max(min(0.5 + ps * 0.4 - vol * 0.1, 1.0), 0.1),
                3
            )

            # ── Actual outcome ──────────────────────────────────────────────────────
            actual = rate_map[dates[i + 7]]
            actual_dir = "up" if actual > current else "down"
            correct = pred_dir == actual_dir

            results.append({
                "prediction_date": pred_date.strftime("%Y-%m-%d"),
                "current_rate": current,
                "predicted_direction": pred_dir,
                "actual_direction": actual_dir,
                "was_correct": correct,
                "confidence": conf,
            })

        if not results:
            return {"message": "No valid backtest windows found"}

        correct = sum(1 for r in results if r["was_correct"])
        total = len(results)
        acc = correct / total if total > 0 else 0.0

        correct_confs = [r["confidence"] for r in results if r["was_correct"]]
        wrong_confs = [r["confidence"] for r in results if not r["was_correct"]]

        return {
            "total_predictions_evaluated": total,
            "correct": correct,
            "accuracy_pct": round(acc * 100, 1),
            "avg_conf_correct": round(mean(correct_confs), 3) if correct_confs else 0.0,
            "avg_conf_wrong": round(mean(wrong_confs), 3) if wrong_confs else 0.0,
            "backtest_period": f"{dates[0]} to {dates[-1]}",
            "note": "Full ensemble backtest (MC + MR + MOM + TR + RSI + BB)"
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}


def run_evaluation(backtest: bool = True) -> Dict[str, Any]:
    if backtest:
        return run_backtest()
    else:
        return {"message": "Live evaluation not useful yet"}