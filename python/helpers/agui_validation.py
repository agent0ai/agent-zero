"""AG-UI Protocol request validation using Pydantic models."""

from typing import Any, Literal
from pydantic import BaseModel, Field


class ContentPart(BaseModel):
    """A single content part in a message."""
    type: str = "input_text"
    text: str | None = None
    # For other content types (images, files, etc.)
    data: Any | None = None
    mime_type: str | None = None


class AguiMessage(BaseModel):
    """An AG-UI protocol message."""
    role: Literal["user", "assistant", "system", "tool"]
    content: list[ContentPart] | str | None = None
    # For tool messages
    tool_call_id: str | None = None
    name: str | None = None


class AguiTool(BaseModel):
    """Tool definition for AG-UI."""
    name: str
    description: str | None = None
    parameters: dict[str, Any] | None = None


class RunAgentInput(BaseModel):
    """Input schema for AG-UI /agui endpoint requests."""
    thread_id: str = Field(alias="threadId")
    run_id: str = Field(alias="runId")
    messages: list[AguiMessage] = Field(default_factory=list)
    tools: list[AguiTool] = Field(default_factory=list)
    context: dict[str, Any] = Field(default_factory=dict)
    # Optional API key in body
    api_key: str | None = None
    # Optional project name
    project: str | None = None
    # Optional agent profile name
    agent_name: str | None = Field(default=None, alias="agentName")

    model_config = {
        "populate_by_name": True,  # Allow both snake_case and camelCase
    }


def validate_agui_request(data: dict[str, Any]) -> RunAgentInput:
    """Validate and parse an AG-UI request payload.

    Args:
        data: Raw request JSON data

    Returns:
        Validated RunAgentInput model

    Raises:
        ValidationError: If the request data is invalid
    """
    return RunAgentInput.model_validate(data)


def extract_user_message(input_data: RunAgentInput) -> str:
    """Extract the user message text from validated input.

    Args:
        input_data: Validated AG-UI input

    Returns:
        Combined user message text from the most recent user message
    """
    # Find the most recent user message
    for msg in reversed(input_data.messages):
        if msg.role == "user":
            if isinstance(msg.content, str):
                return msg.content
            elif isinstance(msg.content, list):
                text_parts = []
                for part in msg.content:
                    if part.type in ("input_text", "text") and part.text:
                        text_parts.append(part.text)
                return "\n".join(text_parts)
    return ""
