"""Main chat screen for Agent Zero TUI."""

from __future__ import annotations

import asyncio

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header

from a0.tui.widgets.message_view import MessageView
from a0.tui.widgets.prompt_editor import PromptEditor
from a0.tui.widgets.tool_panel import ToolPanel


class MainScreen(Screen[None]):
    """Main chat interface."""

    BINDINGS = [
        Binding("ctrl+n", "new_session", "New"),
        Binding("escape", "back_to_menu", "Menu"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()

        with Container(id="main-container"):
            with Vertical(id="chat-panel"):
                yield MessageView(id="messages")

            with Vertical(id="side-panel"):
                yield ToolPanel(id="tools")

        with Container(id="input-area"):
            yield PromptEditor(id="prompt")

        yield Footer()

    async def on_prompt_editor_submit(self, event: PromptEditor.Submit) -> None:
        """Handle prompt submission."""
        message = event.text
        if not message.strip():
            return

        messages = self.query_one("#messages", MessageView)
        messages.add_user_message(message)

        app = self.app
        # Send to Agent Zero
        try:
            response = await app.client.send_message(  # type: ignore[attr-defined]
                message=message,
                context_id=app.context_id or "",  # type: ignore[attr-defined]
                project_name=app.project,  # type: ignore[attr-defined]
            )
            app.context_id = response.context_id  # type: ignore[attr-defined]
            messages.add_agent_message(response.response)

            # Start polling for tool activity
            self.run_worker(self._poll_activity(response.context_id))

        except Exception as e:
            messages.add_error(str(e))

    async def _poll_activity(self, context_id: str) -> None:
        """Poll for agent activity after sending a message."""
        app = self.app
        messages = self.query_one("#messages", MessageView)
        tools = self.query_one("#tools", ToolPanel)

        idle_count = 0
        async for event in app.poller.stream(context_id):  # type: ignore[attr-defined]
            if event.context_reset:
                messages.clear()
                tools.clear()
                break

            for log in event.logs:
                log_type = log.get("type", "")
                agent_no = log.get("agentno", 0)
                content = log.get("content", "")

                if log_type == "response" and agent_no == 0:
                    messages.add_agent_message(content)
                elif log_type == "user":
                    pass  # already shown
                elif log_type == "error":
                    messages.add_error(content)
                elif log_type in {"tool", "code_exe", "browser", "mcp"}:
                    tools.add_tool_step_dict(log)
                else:
                    tools.add_info_step_dict(log)

            if not event.logs and not event.progress_active:
                idle_count += 1
                if idle_count > 6:  # ~3 seconds of idle
                    break
            else:
                idle_count = 0

    def action_new_session(self) -> None:
        """Start a new session."""
        self.app.context_id = None  # type: ignore[attr-defined]
        self.query_one("#messages", MessageView).clear()
        self.query_one("#tools", ToolPanel).clear()
        self.notify("New session started")

    def action_back_to_menu(self) -> None:
        """Return to the launcher menu."""
        self.app.poller.stop()  # type: ignore[attr-defined]
        self.app.exit(result="menu")
