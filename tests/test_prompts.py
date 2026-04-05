from retail_sql_agent.models import SQLTask
from retail_sql_agent.prompts import build_system_message, build_user_prompt


def test_system_prompt_mentions_tool_use() -> None:
    prompt = build_system_message("benchmark")
    assert "execute_sql" in prompt
    assert "benchmark mode" in prompt


def test_user_prompt_includes_question_and_schema() -> None:
    task = SQLTask(question="How many rows?", schema="CREATE TABLE demo(id int);")
    prompt = build_user_prompt(task)
    assert "How many rows?" in prompt
    assert "CREATE TABLE demo" in prompt
