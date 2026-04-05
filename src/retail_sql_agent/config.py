from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


@dataclass(slots=True)
class Settings:
    openai_api_key: str
    openai_model: str = "gpt-4o-mini"
    mode: str = "realistic"
    max_tool_iterations: int = 4
    benchmark_output: Path = Path("results/benchmark_report.csv")
    local_db_path: Path = Path("data/retail_analytics/retail_analytics.db")
    local_schema_path: Path = Path("data/retail_analytics/schema.sql")
    local_tasks_path: Path = Path("data/retail_analytics/questions.json")

    @classmethod
    def from_env(cls) -> "Settings":
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY is not set. Copy .env.example to .env and add your API key."
            )

        mode = os.getenv("SQL_AGENT_MODE", "realistic").strip().lower()
        if mode not in {"benchmark", "realistic"}:
            raise ValueError("SQL_AGENT_MODE must be either 'benchmark' or 'realistic'.")

        max_tool_iterations = int(os.getenv("MAX_TOOL_ITERATIONS", "4"))
        benchmark_output = Path(os.getenv("BENCHMARK_OUTPUT", "results/benchmark_report.csv"))

        return cls(
            openai_api_key=api_key,
            openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip(),
            mode=mode,
            max_tool_iterations=max_tool_iterations,
            benchmark_output=benchmark_output,
            local_db_path=Path(
                os.getenv("LOCAL_DB_PATH", "data/retail_analytics/retail_analytics.db")
            ),
            local_schema_path=Path(
                os.getenv("LOCAL_SCHEMA_PATH", "data/retail_analytics/schema.sql")
            ),
            local_tasks_path=Path(
                os.getenv("LOCAL_TASKS_PATH", "data/retail_analytics/questions.json")
            ),
        )
