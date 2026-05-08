# src/infrastructure/llm/client.py

import time
import random
import sys
from typing import Any, Dict, List, Optional

from openai import OpenAI
from mistralai.client import Mistral  # Migrating to V2
# from mistralai import Mistral
from dotenv import load_dotenv
import os

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY missing in environment variables")
if not MISTRAL_API_KEY:
    raise ValueError("MISTRAL_API_KEY missing in environment variables")


# Clients
openrouter = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

mistral_client = Mistral(
    api_key=MISTRAL_API_KEY,
)


# ── CONFIG: change these 2 lines to swap primary / fallback ──
PRIMARY_CLIENT = mistral_client          # <- change to openrouter
FALLBACK_CLIENT = openrouter             # <- change to mistral_client

PRIMARY_MODEL_DEFAULT = "mistral-small-latest"   # <- default model for primary
FALLBACK_MODEL_DEFAULT = None                      # <- default model for fallback (None = use model_primary arg)


def _is_openrouter_slug(model: Optional[str]) -> bool:
    """Detect if a model string is an OpenRouter-specific slug."""
    if not model:
        return False
    return "/" in model or ":free" in model or ":nitro" in model or model.startswith("openrouter/")


def _resolve_primary_model(model: Optional[str]) -> str:
    """Return a valid Mistral model name, filtering out OpenRouter slugs."""
    if model and not _is_openrouter_slug(model):
        return model
    return PRIMARY_MODEL_DEFAULT


def _resolve_fallback_model(model: Optional[str]) -> Optional[str]:
    """Return a valid OpenRouter model name. Falls back to a known free model if the slug looks invalid."""
    if model and _is_openrouter_slug(model):
        return model
    # If upstream passed a Mistral name, don't send it to OpenRouter
    return FALLBACK_MODEL_DEFAULT or "google/gemma-3-4b-it:free"


def chat_with_fallback(
    messages: List[Dict[str, Any]],
    model_primary: Optional[str] = None,
    tools: Optional[list[dict]] = None,
    tool_choice: str = "auto",
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Primary LLM call with fallback to OpenRouter.
    Supports tool calling (Mistral compatible).
    Returns unified response format including tool_calls when present.
    """
    # ── PRIMARY: Mistral ────────────────────────────────────────────────
    try:
        start = time.time()

        resolved_model = _resolve_primary_model(model_primary)

        kwargs: Dict[str, Any] = {
            "model": resolved_model,
            "messages": messages,
            "temperature": temperature,
            "stream": False,
        }
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        if tools is not None:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = tool_choice

        response = PRIMARY_CLIENT.chat.complete(**kwargs)
        latency = time.time() - start

        msg = response.choices[0].message

        return {
            "content": msg.content,
            "tool_calls": getattr(msg, "tool_calls", None),  # list or None
            "tokens": {
                "input": response.usage.prompt_tokens or 0,
                "output": response.usage.completion_tokens or 0,
                "total": response.usage.total_tokens or 0,
            },
            "latency": latency,
            "model": resolved_model,
        }

    except Exception as exc:
        print(f"⚠️ Primary model {model_primary or PRIMARY_MODEL_DEFAULT} failed: {exc}", file=sys.stderr)

        # Small backoff
        time.sleep(1 + random.random() * 2)

        # ── FALLBACK: OpenRouter ────────────────────────────────────────────
        start = time.time()
        try:
            fallback_model = _resolve_fallback_model(model_primary)

            payload = {
                "model": fallback_model,
                "messages": messages,
                "temperature": temperature,
            }
            if tools is not None:
                payload["tools"] = tools
                payload["tool_choice"] = tool_choice
            if max_tokens is not None:
                payload["max_tokens"] = max_tokens

            res = FALLBACK_CLIENT.chat.completions.create(**payload)
            latency = time.time() - start

            msg = res.choices[0].message

            return {
                "content": msg.content,
                "tool_calls": msg.tool_calls,  # list or None
                "tokens": {
                    "input": res.usage.prompt_tokens or 0,
                    "output": res.usage.completion_tokens or 0,
                    "total": res.usage.total_tokens or 0,
                },
                "latency": latency,
                "model": fallback_model,
            }

        except Exception as fallback_exc:
            if "404" in str(fallback_exc) or "No endpoints" in str(fallback_exc):
                print("Model no longer available — consider updating MODEL_PRIMARY")
            print(f"❌ OpenRouter fallback also failed: {fallback_exc}", file=sys.stderr)
            raise RuntimeError("Both LLM providers failed") from fallback_exc


# Quick test when running the file directly
if __name__ == "__main__":
    test_messages = [
        {"role": "user", "content": "What is 7 * 13?"}
    ]
    try:
        # Test with a bad OpenRouter slug — should auto-correct to Mistral
        resp = chat_with_fallback(test_messages, model_primary="openrouter/free")
        print("Test successful:")
        print(resp)
    except Exception as e:
        print("Test failed:", e)
