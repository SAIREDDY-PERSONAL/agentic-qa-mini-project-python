"""Agentic HCM Chatbot - batch evaluation suite, one test per dataset case."""

import pytest

from agentic_qa.dataset import EvalCase, load_cases
from agentic_qa.judge import judge_chatbot_response
from tests.support import ChatPage, MockAgent

CASES = load_cases()


@pytest.mark.parametrize("tc", CASES, ids=[f"{c.id}-{c.category}" for c in CASES])
def test_chatbot_response(tc: EvalCase, chat_page: ChatPage, mock_agent: MockAgent) -> None:
    mock_agent.respond_with(tc.mock_reply, tc.tool_calls())

    chat_page.goto()
    chat_page.send(tc.prompt)
    chatbot_response_text = chat_page.last_response_text()

    # Tool assertion
    if tc.expected_tool != "none":
        called = [call.tool_name for call in mock_agent.tool_calls]
        assert tc.expected_tool in called, f"expected {tc.expected_tool!r} in {called}"

    # LLM judge evaluation
    result = judge_chatbot_response(
        user_prompt=tc.prompt,
        context=tc.context,
        tool_calls=mock_agent.tool_calls,
        chatbot_response_text=chatbot_response_text,
    )
    score = result.score * 10 if result.score <= 1.0 else result.score

    print(f"\n--- [{tc.id}] Evaluation Report ---")
    print(f"Score: {score}/10 | Grounded: {result.is_grounded} | Helpful: {result.is_helpful}")
    print(f"Reasoning: {result.reasoning}\n")

    if tc.expect_grounded:
        assert result.is_grounded, result.reasoning
    assert score >= tc.min_score, result.reasoning
