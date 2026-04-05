from __future__ import annotations

import csv
from pathlib import Path

from .agent import SQLAgentOrchestrator
from .config import Settings
from .local_sqlite import LocalSQLiteSession
from .models import FeedbackMode


async def run_benchmark(
    settings: Settings,
    num_examples: int,
    mode: FeedbackMode,
    output_path: Path | None = None,
) -> list[dict[str, str]]:
    output = output_path or settings.benchmark_output
    output.parent.mkdir(parents=True, exist_ok=True)

    orchestrator = SQLAgentOrchestrator(settings)
    rows: list[dict[str, str]] = []
    examples_to_run = min(
        num_examples,
        LocalSQLiteSession(
            db_path=settings.local_db_path,
            schema_path=settings.local_schema_path,
            tasks_path=settings.local_tasks_path,
            mode=mode,
        ).question_count,
    )

    try:
        for index in range(examples_to_run):
            session = LocalSQLiteSession(
                db_path=settings.local_db_path,
                schema_path=settings.local_schema_path,
                tasks_path=settings.local_tasks_path,
                mode=mode,
            )
            task = session.reset(task_index=index)
            response = await orchestrator.solve(session=session, task=task)

            final_attempt = session.attempts[-1] if session.attempts else None
            row = {
                "example_index": str(index + 1),
                "mode": mode,
                "question": task.question,
                "status": response.status,
                "attempt_count": str(len(session.attempts)),
                "final_error_category": final_attempt.error_category if final_attempt else "",
                "final_sql": response.final_sql,
                "result_preview": response.result_preview,
            }
            if final_attempt and final_attempt.reward is not None:
                row["reward"] = str(final_attempt.reward)
            rows.append(row)
    finally:
        await orchestrator.close()

    fieldnames = sorted({key for row in rows for key in row.keys()})
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return rows
