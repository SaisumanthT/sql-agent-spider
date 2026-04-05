from __future__ import annotations

import warnings


def suppress_known_library_warnings() -> None:
    """Hide noisy library warnings that do not affect agent correctness.

    AutoGen 0.7.x + structured output can emit a Pydantic serializer warning for the
    OpenAI client's internal `parsed` field even when the agent run succeeds. This is
    cosmetic and makes the benchmark output noisy, so we suppress that specific warning.
    """

    warnings.filterwarnings(
        "ignore",
        message=r"(?s)Pydantic serializer warnings:.*field_name='parsed'.*",
        category=UserWarning,
    )
