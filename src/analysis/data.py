import requests
import json
from datetime import datetime, timedelta

# ===============================
# CONFIG and CACHE
# ===============================

PRIMARY_URL = "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@{date}/{api_version}/currencies/{base}.json"

FALLBACK_URL = (
    "https://{date}.currency-api.pages.dev/{api_version}/currencies/{base}.json"
)

CACHE_FILE = "fx_cache.json"


def load_cache():
    try:
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def save_cache(cache):
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f)


# ===============================
# FX Data Fetching
# ===============================


def get_current_rate(
    base: str = "aud",
    target: str = "inr",
    date: str = "latest",
    api_version: str = "v1",
) -> float:
    """
    Fetch current or historical FX rate.
    """

    base = base.lower()
    target = target.lower()

    cache = load_cache()
    cache_key = f"{date}_{base}_{target}"

    if cache_key in cache:
        return cache[cache_key]

    primary_url = PRIMARY_URL.format(
        date=date, api_version=api_version, base=base
    )

    fallback_url = FALLBACK_URL.format(
        date=date, api_version=api_version, base=base
    )

    try:
        response = requests.get(primary_url, timeout=5)
        response.raise_for_status()
        rate = response.json()[base][target]

    except Exception:
        response = requests.get(fallback_url, timeout=5)
        response.raise_for_status()
        rate = response.json()[base][target]

    # Cache only historical data (not latest)
    if date != "latest":
        cache[cache_key] = rate
        save_cache(cache)

    return rate


def get_historical_rates(
    base: str = "aud",
    target: str = "inr",
    days: int = 40,
) -> list[float]:
    """
    Fetch last N days of historical FX rates.
    """

    rates = []

    for i in range(days, 0, -1):
        date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")

        try:
            rate = get_current_rate(
                base=base,
                target=target,
                date=date,
            )
            rates.append(rate)
        except Exception:
            # Skip failed days silently
            continue

    return rates