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

import json
import time
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


# --- MCP Apps tools ---

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Server Dashboard</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: system-ui, -apple-system, sans-serif; padding: 20px; background: #1a1a2e; color: #e0e0e0; }
  .card { background: #16213e; border-radius: 12px; padding: 16px; margin-bottom: 12px; border: 1px solid #0f3460; }
  .card h3 { color: #e94560; margin-bottom: 8px; font-size: 14px; }
  .card .value { font-size: 28px; font-weight: 700; color: #fff; }
  .card .label { font-size: 12px; color: #888; margin-top: 4px; }
  .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
  h1 { font-size: 18px; margin-bottom: 16px; color: #e94560; }
  button { background: #e94560; color: white; border: none; padding: 10px 20px; border-radius: 8px; cursor: pointer; font-size: 14px; margin-top: 12px; }
  button:hover { background: #c73e54; }
  #status { margin-top: 8px; font-size: 12px; color: #888; }
</style>
</head>
<body>
  <h1>📊 Server Dashboard</h1>
  <div class="grid">
    <div class="card">
      <h3>Server Time</h3>
      <div class="value" id="time">Loading...</div>
      <div class="label">Last updated</div>
    </div>
    <div class="card">
      <h3>Status</h3>
      <div class="value" id="status-val">●</div>
      <div class="label" id="status-label">Checking...</div>
    </div>
    <div class="card">
      <h3>Uptime</h3>
      <div class="value" id="uptime">--</div>
      <div class="label">Hours</div>
    </div>
    <div class="card">
      <h3>Requests</h3>
      <div class="value" id="requests">--</div>
      <div class="label">Total served</div>
    </div>
  </div>
  <button id="refresh-btn">Refresh Data</button>
  <div id="status"></div>

  <script>
    // Simple MCP App client using postMessage JSON-RPC
    let nextId = 1;
    const pending = new Map();

    function sendRequest(method, params) {
      const id = nextId++;
      window.parent.postMessage({ jsonrpc: "2.0", id, method, params }, "*");
      return new Promise((resolve, reject) => {
        pending.set(id, { resolve, reject });
        setTimeout(() => {
          if (pending.has(id)) {
            pending.delete(id);
            reject(new Error("Timeout"));
          }
        }, 10000);
      });
    }

    function sendNotification(method, params) {
      window.parent.postMessage({ jsonrpc: "2.0", method, params }, "*");
    }

    window.addEventListener("message", (event) => {
      const data = event.data;
      if (!data || data.jsonrpc !== "2.0") return;

      // Handle responses
      if (data.id !== undefined && !data.method) {
        const p = pending.get(data.id);
        if (p) {
          pending.delete(data.id);
          if (data.error) p.reject(new Error(data.error.message));
          else p.resolve(data.result);
        }
        return;
      }

      // Handle notifications from host
      if (data.method === "ui/notifications/tool-result") {
        displayResult(data.params);
      }
      if (data.method === "ui/notifications/tool-input") {
        document.getElementById("status").textContent = "Tool input received: " + JSON.stringify(data.params?.arguments || {});
      }
    });

    function displayResult(result) {
      if (!result || !result.content) return;
      const text = result.content.find(c => c.type === "text")?.text || "";
      try {
        const data = JSON.parse(text);
        document.getElementById("time").textContent = data.time || "--";
        document.getElementById("status-val").textContent = data.healthy ? "● Online" : "● Offline";
        document.getElementById("status-val").style.color = data.healthy ? "#4ecca3" : "#e94560";
        document.getElementById("status-label").textContent = data.healthy ? "All systems go" : "Issues detected";
        document.getElementById("uptime").textContent = data.uptime_hours || "--";
        document.getElementById("requests").textContent = data.total_requests || "--";
      } catch {
        document.getElementById("time").textContent = text.slice(0, 30);
      }
    }

    // Initialize: send ui/initialize
    async function init() {
      try {
        const result = await sendRequest("ui/initialize", {
          protocolVersion: "2025-06-18",
          capabilities: {},
          clientInfo: { name: "Dashboard App", version: "1.0.0" },
        });
        sendNotification("ui/notifications/initialized", {});
        document.getElementById("status").textContent = "Connected to host";
      } catch (e) {
        document.getElementById("status").textContent = "Init failed: " + e.message;
      }
    }

    // Refresh button: call server tool
    document.getElementById("refresh-btn").addEventListener("click", async () => {
      document.getElementById("status").textContent = "Refreshing...";
      try {
        const result = await sendRequest("tools/call", {
          name: "get_server_stats",
          arguments: {},
        });
        displayResult(result);
        document.getElementById("status").textContent = "Refreshed at " + new Date().toLocaleTimeString();
      } catch (e) {
        document.getElementById("status").textContent = "Refresh failed: " + e.message;
      }
    });

    init();
  </script>
</body>
</html>"""

_server_start = time.time()
_request_count = 0


@mcp.resource(
    "ui://elicitation-test/dashboard",
    name="Server Dashboard",
    description="Interactive server monitoring dashboard",
    mime_type="text/html",
)
def get_dashboard_html() -> str:
    """Serve the dashboard HTML for the MCP App."""
    return DASHBOARD_HTML


@mcp.tool(
    meta={
        "ui": {
            "resourceUri": "ui://elicitation-test/dashboard",
            "visibility": ["model", "app"],
        }
    }
)
async def show_dashboard(ctx: Context, title: str = "Server Dashboard") -> str:
    """Show an interactive server monitoring dashboard. Returns live server statistics.

    This tool demonstrates MCP Apps — it renders an interactive UI in the host.
    """
    global _request_count
    _request_count += 1
    uptime = (time.time() - _server_start) / 3600
    data = {
        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "healthy": True,
        "uptime_hours": round(uptime, 2),
        "total_requests": _request_count,
    }
    return json.dumps(data)


@mcp.tool(
    meta={
        "ui": {
            "resourceUri": "ui://elicitation-test/dashboard",
            "visibility": ["app"],
        }
    }
)
async def get_server_stats(name: str = "Server") -> str:
    """Get current server statistics. This is an app-only tool (hidden from model).

    Called by the dashboard UI's refresh button.
    """
    global _request_count
    _request_count += 1
    uptime = (time.time() - _server_start) / 3600
    data = {
        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "healthy": True,
        "uptime_hours": round(uptime, 2),
        "total_requests": _request_count,
    }
    return json.dumps(data)


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8100)
