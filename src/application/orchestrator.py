import json
import time
from typing import Dict, Any, List, Optional

from src.config.settings import settings
from src.infrastructure.llm.client import chat_with_fallback
from src.infrastructure.tools.definitions import get_all_tools
from src.infrastructure.tools.executors import TOOL_EXECUTORS
from src.utils.pricing import estimate_model_cost
from src.infrastructure.logging.logger import log_event
from src.domain.models import AgentState


def orchestrator(
    user_input: str,
    conversation_history: List[Dict[str, Any]],
    state: Optional[AgentState] = None,
) -> str:
    """
    Main entry point for the agent.
    Stateful via conversation_history.
    Returns the final answer string.
    """

    if state is None:
        state = AgentState(conversation_history=conversation_history)

    tools = get_all_tools()

    # ─────────────────────────────────────────────────────────────
    # System Prompt
    # ─────────────────────────────────────────────────────────────
    system_content = """You are a helpful FX trading and currency conversion assistant.
You MUST use tools when appropriate.

Rules:

1. For ANY question about current exchange rates, conversion amounts,
INR/USD, INR/AUD, "current rate", "today's rate", "live rate",
"economy now", "FX market now" → ALWAYS call run_fx_analysis.
Never guess or use old knowledge.

2. For ANY question about exchange rates, forecasts, whether to convert,
buy/sell/hold, "good time to convert", direction (up/down), or anything
FX-related → ALWAYS call run_fx_analysis.

Include base_currency and target_currency if mentioned.
If not specified, default to AUD/INR.

ALWAYS include:
- Current rate and pair
- prob_up
- decision
- confidence (0–1)
- risk description

If confidence < 0.6, emphasize uncertainty.

Be concise, professional, and data-driven.
Use the full tool result.

3. You can call multiple tools if needed.

4. After getting tool results, ALWAYS use them in final answer.
Do NOT say "unable to access".
Return plain text only.
"""

    # Ensure system message exists only once at top
    if not conversation_history or conversation_history[0]["role"] != "system":
        conversation_history.insert(0, {"role": "system", "content": system_content})

    conversation_history.append({"role": "user", "content": user_input})

    # ─────────────────────────────────────────────────────────────
    # Tracking
    # ─────────────────────────────────────────────────────────────
    total_input_tokens = 0
    total_output_tokens = 0
    total_latency = 0.0
    model_used = settings.MODEL_PRIMARY
    called_tools: List[str] = []
    fx_data: Optional[Dict] = None
    final_response: str = "No response generated."
    step = 0

    MAX_ITERATIONS = settings.MAX_TOOL_STEPS or 6

    # ─────────────────────────────────────────────────────────────
    # Tool Loop
    # ─────────────────────────────────────────────────────────────
    for step in range(MAX_ITERATIONS):
        start_time = time.time()

        response_dict = chat_with_fallback(
            messages=conversation_history,
            model_primary=settings.MODEL_PRIMARY,
            tools=tools,
            tool_choice="auto",
        )

        latency = time.time() - start_time
        total_latency += latency

        tokens = response_dict.get("tokens", {})
        total_input_tokens += tokens.get("input", 0)
        total_output_tokens += tokens.get("output", 0)

        model_used = response_dict.get("model", model_used)

        assistant_msg = {
            "role": "assistant",
            "content": response_dict.get("content"),
        }

        tool_calls = response_dict.get("tool_calls")

        # If no tool calls → final answer
        if not tool_calls:
            final_response = response_dict.get(
                "content", "No response generated."
            )
            break

        # Attach tool calls to conversation
        assistant_msg["tool_calls"] = []

        for tc in tool_calls:
            func_name = (
                tc.function.name
                if hasattr(tc, "function")
                else tc["function"]["name"]
            )
            arguments = (
                tc.function.arguments
                if hasattr(tc, "function")
                else tc["function"]["arguments"]
            )
            call_id = tc.id if hasattr(tc, "id") else tc.get("id")

            assistant_msg["tool_calls"].append(
                {
                    "id": call_id,
                    "type": "function",
                    "function": {
                        "name": func_name,
                        "arguments": arguments,
                    },
                }
            )

        conversation_history.append(assistant_msg)

        # Execute tools
        for tc in tool_calls:
            func_name = (
                tc.function.name
                if hasattr(tc, "function")
                else tc["function"]["name"]
            )

            raw_args = (
                tc.function.arguments
                if hasattr(tc, "function")
                else tc["function"]["arguments"]
            )

            try:
                args = json.loads(raw_args)
            except Exception:
                args = {}

            called_tools.append(func_name)
            executor = TOOL_EXECUTORS.get(func_name)

            if not executor:
                tool_result = {"error": f"Tool {func_name} not implemented"}
            else:
                try:
                    tool_result = executor(**args)
                    if func_name == "run_fx_analysis":
                        fx_data = tool_result
                except Exception as exc:
                    tool_result = {"error": str(exc)}

            conversation_history.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.id if hasattr(tc, "id") else tc.get("id"),
                    "name": func_name,
                    "content": json.dumps(tool_result, default=str),
                }
            )

    else:
        final_response = (
            "Sorry — reached maximum reasoning steps. "
            "Please try a simpler question."
        )

    # ─────────────────────────────────────────────────────────────
    # Cost Calculation
    # ─────────────────────────────────────────────────────────────
    cost_estimate = estimate_model_cost(
        model=model_used,
        input_tokens=total_input_tokens,
        output_tokens=total_output_tokens,
    )

    # ─────────────────────────────────────────────────────────────
    # Logging
    # ─────────────────────────────────────────────────────────────
    iteration_count = step + 1
    fx_result = fx_data or {}

    log_event(
        user_query=user_input,
        final_response=final_response,
        model_used=model_used,
        input_tokens=total_input_tokens,
        output_tokens=total_output_tokens,
        cost_estimate=cost_estimate,
        latency_seconds=total_latency,
        intent="fx" if fx_result else "general",
        decision=fx_result.get("decision"),
        prob_up=fx_result.get("prob_up"),
        confidence=fx_result.get("confidence"),
        predicted_rate=fx_result.get("expected_7d"),
        predicted_direction=(
            "up"
            if fx_result.get("prob_up", 0) > 0.5
            else "down"
            if fx_result
            else None
        ),
        tools_used=called_tools,
        tool_calls_count=len(called_tools),
        steps=iteration_count,
    )

    return final_response