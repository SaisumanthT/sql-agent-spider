from __future__ import annotations

import json
from pathlib import Path


def test_local_question_bank_exists_and_has_reference_sql() -> None:
    root = Path(__file__).resolve().parents[1]
    questions_path = root / "data" / "retail_analytics" / "questions.json"
    questions = json.loads(questions_path.read_text(encoding="utf-8"))

    assert len(questions) >= 5
    assert all("question" in question for question in questions)
    assert all("reference_sql" in question for question in questions)
