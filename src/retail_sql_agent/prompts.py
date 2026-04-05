from __future__ import annotations

from .models import FeedbackMode, SQLTask


def build_system_message(mode: FeedbackMode) -> str:
    mode_guidance = {
        "benchmark": (
            "You are operating in benchmark mode. Keep using the execute_sql tool until the "
            "tool confirms success or you hit the tool iteration limit."
        ),
        "realistic": (
            "You are operating in realistic mode. A successful execution is enough to stop; "
            "do not assume you have access to a gold answer."
        ),
    }[mode]

    return (
        "You are an expert SQL agent. Use the execute_sql tool to validate every candidate query. "
        "Think carefully about joins, filters, aggregation, and selected columns. "
        "Always call the tool before finalizing an answer. "
        f"{mode_guidance} "
        "When you finish, return a concise structured response with the final SQL and an explanation."
    )


def build_user_prompt(task: SQLTask) -> str:
    return (
        "Below is the schema for a SQL database:\n"
        f"{task.schema}\n\n"
        "Generate a SQL query that answers the following question:\n"
        f"{task.question}\n\n"
        "Use the execute_sql tool to test candidate SQL before returning the final answer."
    )
