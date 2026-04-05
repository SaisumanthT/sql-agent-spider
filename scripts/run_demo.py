from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from retail_sql_agent.agent import SQLAgentOrchestrator
from retail_sql_agent.config import Settings
from retail_sql_agent.local_sqlite import LocalSQLiteSession
from retail_sql_agent.warnings_config import suppress_known_library_warnings


async def main() -> None:
    suppress_known_library_warnings()

    parser = argparse.ArgumentParser(description="Run a single text-to-SQL demo against the local retail analytics database.")
    parser.add_argument(
        "--mode",
        choices=["benchmark", "realistic"],
        default=None,
        help="Execution mode. Defaults to SQL_AGENT_MODE from .env.",
    )
    parser.add_argument(
        "--show-schema",
        action="store_true",
        help="Print the sampled schema before running the agent.",
    )
    parser.add_argument(
        "--question",
        default=None,
        help="Custom English question to run against the retail dataset.",
    )
    args = parser.parse_args()

    settings = Settings.from_env()
    mode = args.mode or settings.mode

    session = LocalSQLiteSession(
        db_path=settings.local_db_path,
        schema_path=settings.local_schema_path,
        tasks_path=settings.local_tasks_path,
        mode=mode,
    )
    try:
        if args.question:
            task = session.reset(custom_question=args.question)
        else:
            task = session.reset()
    except FileNotFoundError as exc:
        print(str(exc))
        return

    if args.question:
        print("\n=== Input Mode ===")
        print("custom question")

    if args.show_schema:
        print("\n=== Schema ===")
        print(task.schema)

    print("\n=== Question ===")
    print(task.question)

    orchestrator = SQLAgentOrchestrator(settings)
    try:
        response = await orchestrator.solve(session=session, task=task)
    finally:
        await orchestrator.close()

    print("\n=== Final Status ===")
    print(response.status)

    print("\n=== Final SQL ===")
    print(response.final_sql)

    print("\n=== Explanation ===")
    print(response.explanation)

    print("\n=== Result Preview ===")
    print(response.result_preview)

    print("\n=== Attempts ===")
    for index, attempt in enumerate(session.attempts, start=1):
        print(f"\nAttempt {index}")
        print(f"Category: {attempt.error_category}")
        if attempt.error_message:
            print(f"Error: {attempt.error_message}")
        print("SQL:")
        print(attempt.sql)


if __name__ == "__main__":
    asyncio.run(main())
