"""Evaluation cases loaded from data/eval_dataset.json."""

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

DATASET_PATH = Path(__file__).resolve().parents[2] / "data" / "eval_dataset.json"


class ToolCall(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    tool_name: str
    args: dict[str, Any] = Field(default_factory=dict)
    result: dict[str, Any] | None = None


class EvalCase(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    id: str
    category: str
    prompt: str
    context: str
    expected_tool: str
    mock_reply: str
    mock_tool_calls: list[ToolCall] | None = None
    min_score: float
    expect_grounded: bool

    def tool_calls(self) -> list[ToolCall]:
        """Tool calls the mocked agent returns; defaults to a single call of the expected tool."""
        if self.mock_tool_calls is not None:
            return self.mock_tool_calls
        if self.expected_tool == "none":
            return []
        return [ToolCall(tool_name=self.expected_tool, args={"employeeId": "1042"})]


def load_cases(path: Path = DATASET_PATH) -> list[EvalCase]:
    return [EvalCase.model_validate(raw) for raw in json.loads(path.read_text())]
