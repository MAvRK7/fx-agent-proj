# src/analysis/sim.py
import math
import random
from typing import List


def monte_carlo_simulation(
    current_rate: float,
    drift: float,
    volatility: float,
    days: int = 7,
    simulations: int = 1000,
) -> List[float]:
    """
    Simple Monte Carlo simulation for price paths.
    Returns list of simulated ending prices after `days`.
    """
    results = []
    for _ in range(simulations):
        price = current_rate
        for _ in range(days):
            shock = random.gauss(drift, volatility)
            price *= math.exp(shock)
        results.append(price)
    return results