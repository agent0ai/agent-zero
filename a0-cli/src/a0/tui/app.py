"""Agent Zero TUI Application.

A terminal interface built with Textual featuring:
- Rich markdown rendering
- Real-time agent activity streaming
- Collapsible tool execution panels
- Session management
"""

from __future__ import annotations

from textual.app import App, ComposeResult
from textual.binding import Binding

from a0.client.api import AgentZeroClient
from a0.client.poller import Poller


class AgentZeroTUI(App[str | None]):
    """Main TUI Application.

    Returns:
        None: User quit the app entirely (Ctrl+Q)
        "menu": User wants to return to launcher menu (Escape)
    """

    CSS_PATH = "styles/theme.tcss"
    TITLE = "Agent Zero"

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit", show=True),
        Binding("ctrl+d", "toggle_dark", "Theme"),
    ]

    def __init__(
        self,
        agent_url: str = "http://localhost:55080", # change from 8080
        api_key: str | None = None,
        project: str | None = None,
        cwd: str = ".",
    ) -> None:
        super().__init__()
        self.agent_url = agent_url
        self.api_key = api_key
        self.project = project
        self.cwd = cwd

        self.client = AgentZeroClient(agent_url, api_key)
        self.poller = Poller(self.client, interval=0.5)
        self.context_id: str | None = None

    def compose(self) -> ComposeResult:
        from a0.tui.screens.main import MainScreen

        yield MainScreen()

    async def on_mount(self) -> None:
        """Check connectivity on mount."""
        ok = await self.client.health()
        if not ok:
            self.notify(
                f"Cannot reach Agent Zero at {self.agent_url}",
                severity="error",
                timeout=5,
            )

    def action_toggle_dark(self) -> None:
        self.dark = not self.dark

    async def on_unmount(self) -> None:
        self.poller.stop()
        await self.client.close()
