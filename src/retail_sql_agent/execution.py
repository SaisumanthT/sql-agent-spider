from __future__ import annotations

import json
from typing import Any


def preview(value: Any, limit: int = 240) -> str:
    rendered = json.dumps(value, ensure_ascii=True, default=str)
    if len(rendered) <= limit:
        return rendered
    return rendered[: limit - 3] + "..."


def classify_error(error_message: str | None, reward: int | None) -> tuple[str, str]:
    if error_message is None and reward == 1:
        return "success", "success"

    if error_message is None and reward == 0:
        return "incorrect_result", "retryable_error"

    lowered = (error_message or "").lower()
    if "syntax" in lowered:
        return "syntax_error", "retryable_error"
    if "no such table" in lowered or "unknown table" in lowered:
        return "table_reference_error", "retryable_error"
    if "no such column" in lowered or "unknown column" in lowered:
        return "column_reference_error", "retryable_error"
    if "ambiguous" in lowered:
        return "ambiguous_reference", "retryable_error"
    return "runtime_error", "retryable_error"
