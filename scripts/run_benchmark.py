from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from retail_sql_agent.benchmark import run_benchmark
from retail_sql_agent.config import Settings
from retail_sql_agent.warnings_config import suppress_known_library_warnings


async def main() -> None:
    suppress_known_library_warnings()

    parser = argparse.ArgumentParser(description="Run a retail text-to-SQL benchmark sample and export CSV.")
    parser.add_argument("--num-examples", type=int, default=10, help="Number of tasks to sample.")
    parser.add_argument(
        "--mode",
        choices=["benchmark", "realistic"],
        default=None,
        help="Execution mode. Defaults to SQL_AGENT_MODE from .env.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional CSV output path. Defaults to BENCHMARK_OUTPUT from .env.",
    )
    args = parser.parse_args()

    settings = Settings.from_env()
    mode = args.mode or settings.mode
    try:
        rows = await run_benchmark(
            settings=settings,
            num_examples=args.num_examples,
            mode=mode,
            output_path=args.output,
        )
    except FileNotFoundError as exc:
        print(str(exc))
        return

    print(f"\nWrote {len(rows)} benchmark rows.")
    print(f"Mode: {mode}")
    print(f"Output: {args.output or settings.benchmark_output}")


if __name__ == "__main__":
    asyncio.run(main())
