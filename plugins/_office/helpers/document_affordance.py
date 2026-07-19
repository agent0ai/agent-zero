from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ArtifactDecision:
    """Deprecated compatibility type for the retired response affordance."""

    kind: str
    fmt: str
    title: str
    content: str
    reason: str


def decide_response_artifact(user_message: Any, response_text: str) -> None:
    """Response text never creates document artifacts.

    File creation is intentionally opt-in through the document_artifact tool.
    This function remains as a compatibility import point for older code and
    tests that still probe the retired affordance.
    """

    return None


def format_created_response(basename: str, path: str) -> str:
    return (
        f"Created **{basename}**.\n\n"
        f"Path: `{path}`"
    )


def is_subordinate_agent(agent: Any) -> bool:
    number = getattr(agent, "number", None)
    if number is not None:
        try:
            return int(number) > 0
        except (TypeError, ValueError):
            pass

    agent_name = str(getattr(agent, "agent_name", "") or "").strip().lower()
    if agent_name.startswith("a") and agent_name[1:].isdigit():
        return int(agent_name[1:]) > 0
    if agent_name.isdigit():
        return int(agent_name) > 0

    get_data = getattr(agent, "get_data", None)
    if callable(get_data):
        try:
            if get_data("_superior") is not None:
                return True
        except Exception:
            pass

    data = getattr(agent, "data", None)
    if isinstance(data, dict) and data.get("_superior") is not None:
        return True

    return False
