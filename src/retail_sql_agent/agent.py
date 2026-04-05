from __future__ import annotations

from typing import Annotated, Any

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import StructuredMessage
from autogen_core.model_context import BufferedChatCompletionContext
from autogen_core.tools import FunctionTool
from autogen_ext.models.openai import OpenAIChatCompletionClient

from .config import Settings
from .models import SQLAgentResponse, SQLTask
from .prompts import build_system_message, build_user_prompt


class SQLAgentOrchestrator:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.model_client = OpenAIChatCompletionClient(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
        )

    async def solve(self, session: Any, task: SQLTask) -> SQLAgentResponse:
        async def execute_sql(
            reflection: Annotated[str, "Short reasoning about how to improve or validate the SQL query."],
            sql: Annotated[str, "SQL query to execute against the active database."],
        ) -> dict[str, Any]:
            """Execute SQL against the active task and return structured feedback."""

            return session.execute_sql(reflection=reflection, sql=sql)

        execute_sql_tool = FunctionTool(
            execute_sql,
            description=(
                "Execute a candidate SQL query against the active database and return the result preview "
                "or structured feedback about why the query needs another revision."
            ),
            strict=True,
        )

        agent = AssistantAgent(
            name="sql_writer",
            model_client=self.model_client,
            tools=[execute_sql_tool],
            system_message=build_system_message(session.mode),
            model_context=BufferedChatCompletionContext(buffer_size=8),
            reflect_on_tool_use=True,
            max_tool_iterations=self.settings.max_tool_iterations,
            output_content_type=SQLAgentResponse,
        )

        result = await agent.run(task=build_user_prompt(task))
        last_message = result.messages[-1]

        if isinstance(last_message, StructuredMessage) and isinstance(
            last_message.content, SQLAgentResponse
        ):
            return last_message.content

        final_sql = session.attempts[-1].sql if session.attempts else ""
        result_preview = session.attempts[-1].result_preview if session.attempts else "[]"
        status = "success" if session.attempts and session.attempts[-1].status == "success" else "needs_review"

        return SQLAgentResponse(
            status=status,
            final_sql=final_sql,
            explanation="Fallback response because the model did not return structured output.",
            result_preview=result_preview,
        )

    async def close(self) -> None:
        await self.model_client.close()
