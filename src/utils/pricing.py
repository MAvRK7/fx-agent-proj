# src/utils/pricing.py
from pathlib import Path
import json
from datetime import datetime, timezone

# Define the log file path once (consistent with logger.py)
LOG_FILE = Path("logs/agent_events.jsonl")

MODEL_PRICING = {
    "stepfun/step-3.5-flash:free": {
        "input_per_million": 0.10,
        "output_per_million": 0.30,
    },
    "mistral-small-latest": {
        "input_per_million": 0.10,
        "output_per_million": 0.20,
    },
    # fallback / default
    "default": {
        "input_per_million": 0.10,
        "output_per_million": 0.30,
    }
}


def estimate_model_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """
    Estimate cost in USD based on input + output tokens.
    Uses per-million-token pricing from MODEL_PRICING.
    """
    pricing = MODEL_PRICING.get(model, MODEL_PRICING["default"])
    
    input_cost = (input_tokens / 1_000_000) * pricing["input_per_million"]
    output_cost = (output_tokens / 1_000_000) * pricing["output_per_million"]
    
    total_cost = input_cost + output_cost
    rounded = round(total_cost, 6)

    # Treat extremely small values as zero
    return 0.0 if rounded < 0.000001 else rounded


def summarize_costs() -> dict:
    """
    Summarize costs from the structured JSONL log file.
    Now includes projected monthly cost (assuming 30 queries/day).
    """
    if not LOG_FILE.exists() or LOG_FILE.stat().st_size == 0:
        return {
            "total_cost_usd": 0.0,
            "total_queries": 0,
            "average_cost_per_query_usd": 0.0,
            "log_file": str(LOG_FILE.absolute()),
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "note": "No logs yet",
            "projected_monthly_cost_usd": 0.0,
            "assumption": "Based on 30 queries per day × 30 days"
        }

    total_cost = 0.0
    count = 0

    with LOG_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entry = json.loads(line)
                    total_cost += entry.get("cost_estimate", 0.0)
                    count += 1
                except json.JSONDecodeError:
                    continue

    avg_cost = total_cost / count if count > 0 else 0.0

    # Monthly projection
    QUERIES_PER_DAY = 30          # ← you can change this or make it a parameter later
    DAYS_PER_MONTH = 30
    projected_monthly = avg_cost * QUERIES_PER_DAY * DAYS_PER_MONTH

    return {
        "total_cost_usd": round(total_cost, 4),
        "total_queries": count,
        "average_cost_per_query_usd": round(avg_cost, 6),
        "log_file": str(LOG_FILE.absolute()),
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "projected_monthly_cost_usd": round(projected_monthly, 4),
        "assumption": f"Based on {QUERIES_PER_DAY} queries/day × {DAYS_PER_MONTH} days"
    }


if __name__ == "__main__":
    # Quick test
    cost = estimate_model_cost("stepfun/step-3.5-flash:free", 500, 200)
    print(f"Estimated cost for test: ${cost:.6f}")
    
    summary = summarize_costs()
    print("\nSummary test:")
    print(summary)