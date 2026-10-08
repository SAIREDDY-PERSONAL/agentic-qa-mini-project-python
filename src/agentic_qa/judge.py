"""LLM-as-judge evaluator for chatbot responses."""

import json
import os
from functools import cache
from typing import Any, cast

from dotenv import load_dotenv
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import Runnable
from pydantic import BaseModel, Field

from agentic_qa.dataset import ToolCall

load_dotenv()

# Fail a stuck judge call instead of hanging the suite (seconds)
JUDGE_TIMEOUT = float(os.getenv("JUDGE_TIMEOUT", "120"))


class ChatbotEval(BaseModel):
    score: float = Field(ge=0, le=10, description="Integer score from 0 to 10.")
    is_grounded: bool = Field(description="True if response uses context/tools accurately.")
    is_helpful: bool = Field(
        description="True if response addresses user prompt within HR boundaries."
    )
    reasoning: str = Field(description="Explanation for score.")


def _create_chat_model() -> BaseChatModel:
    if os.getenv("ANTHROPIC_API_KEY"):
        from langchain_anthropic import ChatAnthropic

        model = os.getenv("ANTHROPIC_MODEL", "claude-haiku-5-5")
        print(f"Using LLM Judge Provider: Anthropic Claude ({model})")
        headers = {}
        if workspace_id := os.getenv("ANTHROPIC_WORKSPACE_ID"):
            headers["anthropic-workspace-id"] = workspace_id
        # temperature is not supported by current Claude models
        return ChatAnthropic(  # type: ignore[call-arg]
            model_name=model, default_headers=headers, default_request_timeout=JUDGE_TIMEOUT
        )

    if os.getenv("OPENAI_API_KEY"):
        from langchain_openai import ChatOpenAI

        print("Using LLM Judge Provider: OpenAI (gpt-4o-mini)")
        return ChatOpenAI(model="gpt-4o-mini", temperature=0, timeout=JUDGE_TIMEOUT)

    from langchain_ollama import ChatOllama

    model = os.getenv("OLLAMA_MODEL", "llama3.2")
    print(f"Using LLM Judge Provider: Local Ollama ({model})")
    return ChatOllama(
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        model=model,
        temperature=0,
        client_kwargs={"timeout": JUDGE_TIMEOUT},
    )


@cache
def _judge_model() -> Runnable[Any, Any]:
    return _create_chat_model().with_structured_output(ChatbotEval)


def judge_chatbot_response(
    *,
    user_prompt: str,
    context: str,
    tool_calls: list[ToolCall],
    chatbot_response_text: str,
) -> ChatbotEval:
    tools_executed = json.dumps(
        [tc.model_dump(by_alias=True, exclude_none=True) for tc in tool_calls]
    )
    system_prompt = f"""
You are an enterprise QA Judge evaluating an HR Enterprise Assistant Chatbot.

User Prompt: "{user_prompt}"
System Context: "{context}"
Tools Executed: {tools_executed}
Chatbot UI Response: "{chatbot_response_text}"

EVALUATION RULES:
1. HR Scope:
   - For HR queries: Evaluate tool usage and response accuracy.
   - For non-HR queries: Politeness in declining is expected; award standard pass scores.
2. Groundedness:
   - Verify responses stay strictly within context and tool outputs without hallucinating.
"""
    return cast(ChatbotEval, _judge_model().invoke(system_prompt))
