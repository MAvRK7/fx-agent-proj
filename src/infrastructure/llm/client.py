# src/infrastructure/llm/client.py

import time
import random
import sys
from typing import Any, Dict, List, Optional

from openai import OpenAI
from mistralai import Mistral
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

mistral = Mistral(
    api_key=MISTRAL_API_KEY,
)


def chat_with_fallback(
    messages: List[Dict[str, Any]],
    model_primary: str = "stepfun/step-3.5-flash:free",
    tools: Optional[List[Dict]] = None,
    tool_choice: str = "auto",
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Primary LLM call with fallback to Mistral.
    Supports tool calling (OpenRouter compatible).
    Returns unified response format including tool_calls when present.
    """
    payload = {
        "model": model_primary,
        "messages": messages,
        "temperature": temperature,
    }

    if tools is not None:
        payload["tools"] = tools
        payload["tool_choice"] = tool_choice

    if max_tokens is not None:
        payload["max_tokens"] = max_tokens

    try:
        # ── PRIMARY: OpenRouter ─────────────────────────────────────────────
        start = time.time()
        response = openrouter.chat.completions.create(**payload)
        latency = time.time() - start

        msg = response.choices[0].message

        result = {
            "content": msg.content,
            "tool_calls": msg.tool_calls,  # list or None
            "tokens": {
                "input": response.usage.prompt_tokens or 0,
                "output": response.usage.completion_tokens or 0,
                "total": response.usage.total_tokens or 0,
            },
            "latency": latency,
            "model": model_primary,
        }

        return result

    except Exception as exc:
        print(f"⚠️ OpenRouter failed: {exc}", file=sys.stderr)

        # Small backoff
        time.sleep(1 + random.random() * 2)

        # ── FALLBACK: Mistral (no tool support) ─────────────────────────────
        start = time.time()
        try:
            res = mistral.chat.complete(
                model="mistral-small-latest",
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=False,
            )
            latency = time.time() - start

            return {
                "content": res.choices[0].message.content,
                "tool_calls": None,
                "tokens": {
                    "input": res.usage.prompt_tokens or 0,
                    "output": res.usage.completion_tokens or 0,
                    "total": res.usage.total_tokens or 0,
                },
                "latency": latency,
                "model": "mistral-small-latest",
            }

        except Exception as fallback_exc:
            print(f"❌ Mistral fallback also failed: {fallback_exc}", file=sys.stderr)
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