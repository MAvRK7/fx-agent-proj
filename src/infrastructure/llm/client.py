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

        # Mistral uses 'tools' and 'tool_choice' in the same way
        kwargs: Dict[str, Any] = {
            "model": model_primary or "mistral-small-latest",
            "messages": messages,
            "temperature": temperature,
            "stream": False,
        }
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        if tools is not None:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = tool_choice

        response = mistral_client.chat.complete(**kwargs)
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
            "model": kwargs["model"],
        }

    except Exception as exc:
        print(f"⚠️ Primary model {model_primary or 'mistral-small-latest'} failed: {exc}", file=sys.stderr)

        # Small backoff
        time.sleep(1 + random.random() * 2)

        # ── FALLBACK: OpenRouter ────────────────────────────────────────────
        start = time.time()
        try:
            payload = {
                "model": model_primary,  # whatever free model you pass in
                "messages": messages,
                "temperature": temperature,
            }
            if tools is not None:
                payload["tools"] = tools
                payload["tool_choice"] = tool_choice
            if max_tokens is not None:
                payload["max_tokens"] = max_tokens

            res = openrouter.chat.completions.create(**payload)
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
                "model": model_primary,
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
        resp = chat_with_fallback(test_messages)
        print("Test successful:")
        print(resp)
    except Exception as e:
        print("Test failed:", e)
