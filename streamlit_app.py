from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from retail_sql_agent.agent import SQLAgentOrchestrator
from retail_sql_agent.config import Settings
from retail_sql_agent.local_sqlite import LocalSQLiteSession
from retail_sql_agent.warnings_config import suppress_known_library_warnings


suppress_known_library_warnings()


RETAIL_QUESTIONS_PATH = ROOT / "data" / "retail_analytics" / "questions.json"


def load_settings() -> Settings:
    return Settings.from_env()


def load_retail_examples() -> list[dict[str, str]]:
    if not RETAIL_QUESTIONS_PATH.exists():
        return []
    return json.loads(RETAIL_QUESTIONS_PATH.read_text(encoding="utf-8"))


def rows_to_dataframe(columns: list[str], rows: list[tuple[Any, ...]]) -> pd.DataFrame:
    if columns:
        return pd.DataFrame(rows, columns=columns)
    return pd.DataFrame(rows)


def build_retail_preview(settings: Settings) -> dict[str, Any]:
    session = LocalSQLiteSession(
        db_path=settings.local_db_path,
        schema_path=settings.local_schema_path,
        tasks_path=settings.local_tasks_path,
        mode="realistic",
    )
    tables = session.list_tables()
    previews: list[dict[str, Any]] = []
    for table_name in tables:
        columns, rows = session.sample_table(table_name, limit=5)
        previews.append(
            {
                "table_name": table_name,
                "columns": columns,
                "rows": rows,
            }
        )
    return {
        "title": "Retail Analytics SQLite Database",
        "subtitle": "Sample records from customers, products, orders, payments, and support tickets.",
        "tables": previews,
        "schema": settings.local_schema_path.read_text(encoding="utf-8"),
    }


async def run_demo(
    settings: Settings,
    mode: str,
    question_text: str,
    selected_question_id: str | None,
) -> dict[str, Any]:
    effective_mode = mode if selected_question_id else "realistic"
    session = LocalSQLiteSession(
        db_path=settings.local_db_path,
        schema_path=settings.local_schema_path,
        tasks_path=settings.local_tasks_path,
        mode=effective_mode,
    )

    if selected_question_id:
        task = session.reset(question_id=selected_question_id)
    else:
        task = session.reset(custom_question=question_text)

    orchestrator = SQLAgentOrchestrator(settings)
    try:
        response = await orchestrator.solve(session=session, task=task)
    finally:
        await orchestrator.close()

    result_columns: list[str] = []
    result_rows: list[tuple[Any, ...]] = []
    result_error: str | None = None
    if response.final_sql.strip():
        try:
            result_columns, result_rows = session.query_with_columns(response.final_sql)
        except Exception as exc:  # pragma: no cover
            result_error = str(exc)

    return {
        "task": task,
        "response": response,
        "attempts": session.attempts,
        "mode": effective_mode,
        "used_sample_prompt": bool(selected_question_id),
        "result_columns": result_columns,
        "result_rows": result_rows,
        "result_error": result_error,
    }


st.set_page_config(page_title="Retail SQL Agent", layout="wide")

st.markdown(
    """
    <style>
    .block-container {padding-top: 2rem; padding-bottom: 2rem; max-width: 1200px;}
    .hero {
        padding: 1.25rem 1.5rem;
        border: 1px solid #d7e3ef;
        border-radius: 18px;
        background: linear-gradient(135deg, #f7fbff 0%, #eef6ff 100%);
        margin-bottom: 1.25rem;
    }
    .hero h1 {margin: 0 0 0.35rem 0; color: #103652; font-size: 2rem;}
    .hero p {margin: 0; color: #355873; font-size: 1rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
      <h1>Retail SQL Agent</h1>
      <p>Preview the database, ask a question in English, and inspect the generated SQL, answer, and explanation.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

try:
    settings = load_settings()
except ValueError as exc:
    st.error(str(exc))
    st.stop()

retail_examples = load_retail_examples()
if "question_input" not in st.session_state:
    st.session_state["question_input"] = ""
if "selected_retail_question_id" not in st.session_state:
    st.session_state["selected_retail_question_id"] = None

top_left, top_right = st.columns(2)
with top_left:
    dataset_label = st.selectbox("Dataset", ["Retail Analytics"], index=0)
with top_right:
    mode = st.selectbox("Mode", ["realistic", "benchmark"], index=0)

st.caption(
    "Use built-in sample prompts with `benchmark` mode when you want exact-answer evaluation. "
    "Use your own free-text question with `realistic` mode for the smoothest demo."
)

st.subheader("Database Preview")
try:
    preview = build_retail_preview(settings)
except FileNotFoundError as exc:
    st.error(str(exc))
    st.info("Run `python scripts/setup_local_db.py` first to create the local SQLite database.")
    st.stop()

st.write(preview["title"])
st.caption(preview["subtitle"])

preview_tabs = st.tabs([item["table_name"] for item in preview["tables"]])
for tab, table_preview in zip(preview_tabs, preview["tables"]):
    with tab:
        st.dataframe(
            rows_to_dataframe(table_preview["columns"], table_preview["rows"]),
            use_container_width=True,
            hide_index=True,
        )

with st.expander("Show schema", expanded=False):
    st.code(preview["schema"], language="sql")

st.subheader("Ask a Question")
st.write("Type your own English question or click one of the sample prompts below.")

question_input = st.text_area(
    "Question in English",
    key="question_input",
    height=110,
    placeholder="Example: Which customers used invoice payments for at least one paid order?",
)

st.write("Sample prompts")
prompt_columns = st.columns(2)
for index, example in enumerate(retail_examples):
    with prompt_columns[index % 2]:
        if st.button(example["question"], key=f"retail_prompt_{example['id']}", use_container_width=True):
            st.session_state["question_input"] = example["question"]
            st.session_state["selected_retail_question_id"] = example["id"]
            st.rerun()

matched_example = next(
    (item["id"] for item in retail_examples if item["question"].strip() == question_input.strip()),
    None,
)
st.session_state["selected_retail_question_id"] = matched_example

if st.button("Generate SQL", type="primary", use_container_width=True):
    if not question_input.strip():
        st.warning("Enter a question in English or click one of the sample prompts first.")
    else:
        try:
            with st.spinner("Generating SQL and validating it against the retail database..."):
                st.session_state["last_run"] = asyncio.run(
                    run_demo(
                        settings=settings,
                        mode=mode,
                        question_text=question_input.strip(),
                        selected_question_id=st.session_state.get("selected_retail_question_id"),
                    )
                )
        except Exception as exc:  # pragma: no cover
            st.error(f"Run failed: {exc}")

if "last_run" in st.session_state:
    run = st.session_state["last_run"]
    response = run["response"]
    attempts = run["attempts"]

    st.divider()
    stat_1, stat_2, stat_3 = st.columns(3)
    with stat_1:
        st.metric("Dataset", dataset_label)
    with stat_2:
        st.metric("Mode Used", run["mode"])
    with stat_3:
        st.metric("Attempts", len(attempts))

    if not run["used_sample_prompt"] and run["mode"] != mode:
        st.info(
            "Custom questions are run in realistic mode so the agent relies on execution feedback "
            "instead of benchmark reference answers."
        )

    st.subheader("Answer")
    if run["result_error"]:
        st.warning(f"Could not render the final table view: {run['result_error']}")
        st.code(response.result_preview, language="json")
    elif run["result_rows"] or run["result_columns"]:
        answer_df = rows_to_dataframe(run["result_columns"], run["result_rows"])
        st.dataframe(answer_df, use_container_width=True, hide_index=True)
        st.caption(f"{len(answer_df)} row(s) returned.")
    else:
        st.code(response.result_preview, language="json")

    st.subheader("SQL")
    st.code(response.final_sql, language="sql")

    st.subheader("Explanation")
    st.write(response.explanation)

    with st.expander("Debug Trace", expanded=False):
        for index, attempt in enumerate(attempts, start=1):
            st.markdown(f"**Attempt {index}**")
            st.write(f"Category: `{attempt.error_category}`")
            st.write(f"Status: `{attempt.status}`")
            if attempt.error_message:
                st.write(f"Error: {attempt.error_message}")
            st.code(attempt.sql, language="sql")
            st.code(attempt.result_preview, language="json")
