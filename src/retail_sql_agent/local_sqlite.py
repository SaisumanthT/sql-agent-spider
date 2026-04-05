from __future__ import annotations

import json
import random
import sqlite3
from pathlib import Path
from typing import Any

from .execution import classify_error, preview
from .models import FeedbackMode, SQLAttempt, SQLTask


def _normalize_rows(rows: list[tuple[Any, ...]]) -> list[str]:
    return sorted(json.dumps(list(row), ensure_ascii=True, default=str) for row in rows)


class LocalSQLiteSession:
    """Run the SQL agent against a self-contained local analytics database."""

    def __init__(
        self,
        db_path: Path,
        schema_path: Path,
        tasks_path: Path,
        mode: FeedbackMode = "realistic",
        random_seed: int = 7,
    ) -> None:
        self.db_path = Path(db_path)
        self.schema_path = Path(schema_path)
        self.tasks_path = Path(tasks_path)
        self.mode = mode
        self.random = random.Random(random_seed)
        self.attempts: list[SQLAttempt] = []
        self.current_task: SQLTask | None = None
        self._questions = self._load_questions()

    def _load_questions(self) -> list[dict[str, Any]]:
        return json.loads(self.tasks_path.read_text(encoding="utf-8"))

    @property
    def question_count(self) -> int:
        return len(self._questions)

    def _ensure_db_exists(self) -> None:
        if not self.db_path.exists():
            raise FileNotFoundError(
                f"Local database not found at {self.db_path}. Run scripts/setup_local_db.py first."
            )

    def _execute_query(self, sql: str) -> list[tuple[Any, ...]]:
        self._ensure_db_exists()
        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.cursor()
            cursor.execute(sql)
            rows = cursor.fetchall()
        return rows

    def query_with_columns(self, sql: str) -> tuple[list[str], list[tuple[Any, ...]]]:
        self._ensure_db_exists()
        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.cursor()
            cursor.execute(sql)
            rows = cursor.fetchall()
            columns = [column[0] for column in cursor.description] if cursor.description else []
        return columns, rows

    def list_tables(self) -> list[str]:
        self._ensure_db_exists()
        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
            )
            return [row[0] for row in cursor.fetchall()]

    def sample_table(self, table_name: str, limit: int = 5) -> tuple[list[str], list[tuple[Any, ...]]]:
        quoted_table = '"' + table_name.replace('"', '""') + '"'
        return self.query_with_columns(f"SELECT * FROM {quoted_table} LIMIT {int(limit)}")

    def reset(
        self,
        task_index: int | None = None,
        question_id: str | None = None,
        custom_question: str | None = None,
    ) -> SQLTask:
        self.attempts = []
        self._ensure_db_exists()

        if custom_question is not None:
            selected = {
                "id": "custom_question",
                "question": custom_question.strip(),
                "custom_question": True,
            }
        elif question_id is not None:
            selected = next(question for question in self._questions if question["id"] == question_id)
        elif task_index is not None:
            selected = self._questions[task_index % len(self._questions)]
        else:
            selected = self.random.choice(self._questions)

        schema = self.schema_path.read_text(encoding="utf-8")
        self.current_task = SQLTask(question=selected["question"], schema=schema, metadata=selected)
        return self.current_task

    def execute_sql(self, reflection: str, sql: str) -> dict[str, Any]:
        if self.current_task is None:
            raise RuntimeError("Call reset() before execute_sql().")

        result_rows: list[tuple[Any, ...]] = []
        execution_error: str | None = None
        reward: int | None = None
        expected_preview: str | None = None

        try:
            result_rows = self._execute_query(sql)
            if self.mode == "benchmark" and "reference_sql" in self.current_task.metadata:
                expected_rows = self._execute_query(self.current_task.metadata["reference_sql"])
                reward = int(_normalize_rows(result_rows) == _normalize_rows(expected_rows))
                expected_preview = preview(expected_rows)
                if reward == 0:
                    execution_error = (
                        "The SQL executed successfully but did not match the expected answer for this local task. "
                        "Double-check the selected columns, filters, ordering, joins, and aggregation logic."
                    )
            else:
                reward = 1 if self.mode == "realistic" else None
        except sqlite3.Error as exc:
            execution_error = str(exc)
            reward = 0

        status_reward = reward if reward is not None else 1
        error_category, status = classify_error(execution_error, status_reward)
        attempt = SQLAttempt(
            reflection=reflection,
            sql=sql,
            status=status,
            error_category=error_category,
            error_message=execution_error,
            reward=reward if self.mode == "benchmark" else None,
            result_preview=preview(result_rows),
            gold_result_preview=expected_preview if self.mode == "benchmark" else None,
        )
        self.attempts.append(attempt)

        payload: dict[str, Any] = {
            "status": status,
            "error_category": error_category,
            "sql": sql,
            "result_preview": attempt.result_preview,
        }
        if execution_error is not None:
            payload["error"] = execution_error
        if self.mode == "benchmark":
            payload["reward"] = reward
            payload["expected_result_preview"] = expected_preview

        return payload
