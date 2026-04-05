from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from pydantic import BaseModel, Field


FeedbackMode = Literal["benchmark", "realistic"]
ExecutionStatus = Literal["success", "retryable_error", "final_error"]


@dataclass(slots=True)
class SQLTask:
    question: str
    schema: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class SQLAttempt:
    reflection: str
    sql: str
    status: ExecutionStatus
    error_category: str
    error_message: str | None
    reward: int | None
    result_preview: str
    gold_result_preview: str | None = None


class SQLAgentResponse(BaseModel):
    status: Literal["success", "needs_review"] = Field(
        description="Whether the query appears correct or still needs manual review."
    )
    final_sql: str = Field(description="The final SQL query.")
    explanation: str = Field(
        description="A short explanation of how the query works and why it was chosen."
    )
    result_preview: str = Field(
        description="A compact preview of the query result or the latest execution feedback."
    )
