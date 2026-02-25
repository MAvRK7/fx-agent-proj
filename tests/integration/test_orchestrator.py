# tests/integration/test_orchestrator.py

import pytest
from unittest.mock import patch, MagicMock
from src.application.orchestrator import orchestrator
from src.domain.models import AgentState


@pytest.fixture
def mock_state():
    return AgentState(
        conversation_history=[{"role": "system", "content": "You are a test agent."}],
        last_fx_result=None,
        total_cost=0.0,
        eval_feedback=[],
    )


@patch("src.application.orchestrator.log_event")
@patch("src.application.orchestrator.chat_with_fallback")
def test_orchestrator_math_tool_called(mock_chat, mock_log, mock_state):

    # Copy history to avoid mutation leakage
    history = list(mock_state.conversation_history)

    mock_chat.side_effect = [
        {
            "content": None,
            "tool_calls": [
                MagicMock(
                    id="call_math",
                    function=MagicMock(
                        name="calculate_expression",
                        arguments='{"expression": "2 + 3 * 4"}',
                    ),
                )
            ],
            "tokens": {"input": 40, "output": 15},
            "model": "gpt-test",
        },
        {
            "content": "The result of 2 + 3 * 4 is 14.",
            "tool_calls": None,
            "tokens": {"input": 60, "output": 12},
            "model": "gpt-test",
        },
    ]

    response = orchestrator(
        user_input="what is 2 + 3 * 4?",
        conversation_history=history,
        state=mock_state,
    )

    assert "14" in response
    assert mock_chat.call_count == 2
    mock_log.assert_called_once()


@patch("src.application.orchestrator.log_event")
@patch("src.application.orchestrator.chat_with_fallback")
def test_orchestrator_fx_tool_called_and_result_used(
    mock_chat,
    mock_log,
    mock_state,
):

    history = list(mock_state.conversation_history)

    mock_fx_result = {
        "pair": "INR/USD",
        "current_rate": 0.012,
        "prob_up": 0.65,
        "decision": "wait",
        "confidence": 0.78,
        "risk": "low volatility (higher confidence)",
    }

    # Patch TOOL_EXECUTORS safely as dict
    with patch.dict(
        "src.application.orchestrator.TOOL_EXECUTORS",
        {"run_fx_analysis": lambda **kwargs: mock_fx_result},
        clear=True,
    ):

        mock_chat.side_effect = [
            {
                "content": None,
                "tool_calls": [
                    MagicMock(
                        id="call_fx",
                        function=MagicMock(
                            name="run_fx_analysis",
                            arguments='{"base_currency": "INR", "target_currency": "USD"}',
                        ),
                    )
                ],
                "tokens": {"input": 40, "output": 15},
                "model": "gpt-test",
            },
            {
                "content": (
                    "Current INR/USD rate is 0.012. "
                    "Prob up 65%, decision: wait "
                    "(low volatility, confidence 78%)."
                ),
                "tool_calls": None,
                "tokens": {"input": 50, "output": 10},
                "model": "gpt-test",
            },
        ]

        response = orchestrator(
            user_input="current INR to USD rate?",
            conversation_history=history,
            state=mock_state,
        )

        assert "0.012" in response
        assert "wait" in response.lower()
        assert "confidence" in response.lower()

    mock_log.assert_called_once()