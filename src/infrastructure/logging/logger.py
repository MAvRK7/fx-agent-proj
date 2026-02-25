# src/infrastructure/logging/logger.py
import json
import time
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Union

from pydantic import BaseModel, Field

from src.config.settings import settings


class LogEntry(BaseModel):
    """Structured log entry model (Pydantic for validation + serialization)"""

    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    session_id: Optional[str] = None                    # future: multi-session support
    user_query: str
    final_response: Optional[str] = None
    intent: Optional[str] = None                        # "fx", "math", "general", "mixed", ...
    decision: Optional[str] = None
    prob_up: Optional[float] = None
    confidence: Optional[float] = None
    predicted_rate: Optional[float] = None
    predicted_direction: Optional[str] = None

    # LLM / cost metrics
    model_used: str
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cost_estimate: float = 0.0
    latency_seconds: float = 0.0

    # Agentic / tool usage
    tools_used: list[str] = Field(default_factory=list)
    tool_calls_count: int = 0
    steps: int = 0                                      # number of ReAct steps

    # Optional rich context
    conversation_length: Optional[int] = None
    error: Optional[str] = None
    extra: Dict[str, Any] = Field(default_factory=dict)


LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "agent_events.jsonl"


def ensure_log_directory() -> None:
    """Create logs directory if it doesn't exist"""
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def log_event(
    user_query: str,
    model_used: str,
    input_tokens: int = 0,
    output_tokens: int = 0,
    cost_estimate: float = 0.0,
    latency_seconds: float = 0.0,
    final_response: Optional[str] = None,
    intent: Optional[str] = None,
    decision: Optional[str] = None,
    prob_up: Optional[float] = None,
    confidence: Optional[float] = None,
    predicted_rate: Optional[float] = None,
    predicted_direction: Optional[str] = None,
    tools_used: Optional[list[str]] = None,
    tool_calls_count: int = 0,
    steps: int = 0,
    session_id: Optional[str] = None,
    conversation_length: Optional[int] = None,
    error: Optional[str] = None,
    **extra: Any,
) -> None:
    """
    Append a structured JSONL log entry.

    Designed to be called at the end of each user turn in the agent loop.
    """
    ensure_log_directory()

    entry = LogEntry(
        user_query=user_query.strip(),
        final_response=final_response,
        intent=intent,
        decision=decision,
        prob_up=round(float(prob_up), 4) if prob_up is not None else None,
        confidence=round(float(confidence), 4) if confidence is not None else None,
        predicted_rate=round(float(predicted_rate), 4) if predicted_rate is not None else None,
        predicted_direction=predicted_direction,
        model_used=model_used,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=input_tokens + output_tokens,
        cost_estimate=round(float(cost_estimate), 6),
        latency_seconds=round(float(latency_seconds), 3),
        tools_used=tools_used or [],
        tool_calls_count=tool_calls_count,
        steps=steps,
        session_id=session_id,
        conversation_length=conversation_length,
        error=error,
        extra=extra,
    )

    try:
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(entry.model_dump_json(exclude_none=True) + "\n")
    except Exception as exc:
        # Last-resort fallback — don't crash the app
        print(f"[LOGGER ERROR] Failed to write log: {exc}", file=sys.stderr)
        print(json.dumps(entry.model_dump(exclude_none=True), indent=2), file=sys.stderr)


def log_summary() -> Dict[str, Any]:
    """Quick utility to summarize costs & usage (can be called from CLI or dashboard)"""
    if not LOG_FILE.exists():
        return {"total_cost": 0.0, "queries": 0, "avg_cost": 0.0}

    total_cost = 0.0
    count = 0

    with LOG_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    entry = json.loads(line)
                    total_cost += entry.get("cost_estimate", 0)
                    count += 1
                except json.JSONDecodeError:
                    continue

    avg_cost = total_cost / count if count > 0 else 0.0

    return {
        "total_cost_usd": round(total_cost, 4),
        "total_queries": count,
        "average_cost_per_query": round(avg_cost, 6),
        "log_file": str(LOG_FILE),
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }


if __name__ == "__main__":
    # Quick test / demo
    log_event(
        user_query="Should I send money to India today?",
        model_used="stepfun/step-3.5-flash:free",
        input_tokens=320,
        output_tokens=180,
        cost_estimate=0.000042,
        latency_seconds=2.84,
        intent="fx",
        decision="wait (expected improvement)",
        prob_up=0.62,
        confidence=0.78,
        tools_used=["run_fx_analysis"],
        steps=2,
    )

    print(log_summary())