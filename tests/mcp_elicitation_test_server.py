#!/usr/bin/env python3
"""
Simple MCP server for end-to-end testing of the elicitation feature.

Usage:
  Start the server:
    python tests/mcp_elicitation_test_server.py

  Add to Agent Zero MCP config as:
    {
      "name": "elicitation-test",
      "type": "streamable-http",
      "url": "http://localhost:8100/mcp"
    }

Tools provided:
  - greet_user: Elicits user's name and greeting style, returns a personalized greeting.
  - create_task: Elicits task details (title, priority, description), returns summary.
  - confirm_action: Elicits a yes/no confirmation before proceeding.
  - simple_echo: No elicitation, just echoes input (control test).
"""

from enum import Enum
from typing import Optional

from fastmcp import FastMCP, Context
from fastmcp.server.elicitation import AcceptedElicitation
from mcp.types import TextContent, SamplingMessage
from pydantic import BaseModel, Field


mcp = FastMCP(
    name="elicitation-test",
    instructions="A test server for MCP elicitation. Use the tools to test human-in-the-loop input gathering.",
)


# --- Elicitation response models ---

class GreetingInfo(BaseModel):
    name: str = Field(description="Your name")
    style: str = Field(description="Greeting style: formal, casual, or pirate")


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TaskInfo(BaseModel):
    title: str = Field(description="Task title")
    priority: Priority = Field(default=Priority.MEDIUM, description="Task priority level")
    description: str = Field(default="", description="Optional task description")


class Confirmation(BaseModel):
    confirmed: bool = Field(description="Do you want to proceed?")


# --- Tools ---

@mcp.tool()
async def greet_user(ctx: Context, reason: str = "general") -> str:
    """Generate a personalized greeting. Will ask for the user's name and preferred greeting style.

    Args:
        reason: Why the greeting is being generated (e.g. 'welcome', 'farewell', 'general').
    """
    result = await ctx.elicit(
        message="I'd like to greet you! Please provide your name and preferred greeting style.",
        response_type=GreetingInfo,
    )

    if isinstance(result, AcceptedElicitation):
        name = result.data.name
        style = result.data.style.lower()
        if style == "formal":
            return f"Good day, {name}. It is a pleasure to make your acquaintance."
        elif style == "pirate":
            return f"Ahoy, {name}! Welcome aboard, ye scallywag!"
        else:
            return f"Hey {name}! What's up?"
    else:
        return f"Greeting cancelled (action: {result.action})."


@mcp.tool()
async def create_task(ctx: Context, project: str = "default") -> str:
    """Create a new task. Will ask for task details via elicitation.

    Args:
        project: The project to create the task in.
    """
    result = await ctx.elicit(
        message=f"Please provide details for the new task in project '{project}'.",
        response_type=TaskInfo,
    )

    if isinstance(result, AcceptedElicitation):
        task = result.data
        return (
            f"Task created in '{project}':\n"
            f"  Title: {task.title}\n"
            f"  Priority: {task.priority.value}\n"
            f"  Description: {task.description or '(none)'}"
        )
    else:
        return f"Task creation cancelled (action: {result.action})."


@mcp.tool()
async def confirm_action(action_description: str, ctx: Context) -> str:
    """Ask for user confirmation before performing an action.

    Args:
        action_description: Description of the action that needs confirmation.
    """
    result = await ctx.elicit(
        message=f"Please confirm: {action_description}",
        response_type=Confirmation,
    )

    if isinstance(result, AcceptedElicitation):
        if result.data.confirmed:
            return f"Action confirmed: {action_description}. Proceeding."
        else:
            return f"User explicitly declined via the form for: {action_description}."
    else:
        return f"Confirmation cancelled (action: {result.action})."


@mcp.tool()
async def simple_echo(message: str) -> str:
    """Echo the input message back. No elicitation involved (control test).

    Args:
        message: The message to echo.
    """
    return f"Echo: {message}"


# --- Sampling tools ---

@mcp.tool()
async def summarize_text(ctx: Context, text: str) -> str:
    """Summarize a piece of text using the client's LLM via MCP sampling.

    Args:
        text: The text to summarize.
    """
    result = await ctx.sample(
        messages=[
            SamplingMessage(
                role="user",
                content=TextContent(type="text", text=f"Please summarize the following text in 2-3 sentences:\n\n{text}"),
            )
        ],
        system_prompt="You are a concise summarizer. Respond only with the summary.",
        max_tokens=256,
        temperature=0.3,
    )
    return f"Summary: {result.text}"


@mcp.tool()
async def analyze_sentiment(ctx: Context, text: str) -> str:
    """Analyze the sentiment of text using the client's LLM via MCP sampling.

    Args:
        text: The text to analyze.
    """
    result = await ctx.sample(
        messages=[
            SamplingMessage(
                role="user",
                content=TextContent(type="text", text=f"Analyze the sentiment of this text and respond with one word (positive, negative, or neutral) followed by a brief explanation:\n\n{text}"),
            )
        ],
        system_prompt="You are a sentiment analysis expert. Be concise.",
        max_tokens=128,
        temperature=0.0,
    )
    return f"Sentiment analysis: {result.text}"


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8100)
