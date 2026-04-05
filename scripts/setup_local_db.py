from __future__ import annotations

import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATASET_DIR = ROOT / "data" / "retail_analytics"
DB_PATH = DATASET_DIR / "retail_analytics.db"
SCHEMA_PATH = DATASET_DIR / "schema.sql"
SEED_PATH = DATASET_DIR / "seed.sql"


def main() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()

    with sqlite3.connect(DB_PATH) as connection:
        connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        connection.executescript(SEED_PATH.read_text(encoding="utf-8"))
        connection.commit()

    print(f"Created local SQLite database at: {DB_PATH}")


if __name__ == "__main__":
    main()
