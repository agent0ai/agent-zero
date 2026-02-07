"""Action handlers for the launcher menu.

Each action corresponds to a menu option: Chat, Status, Docker, Settings.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING

from rich.console import Console
from rich.prompt import Confirm

if TYPE_CHECKING:
    from a0.client.api import AgentZeroClient


def check_health(url: str, api_key: str | None, timeout: float = 0.5) -> bool:
    """Check if Agent Zero is reachable.

    Args:
        url: Agent Zero URL
        api_key: Optional API key
        timeout: Request timeout in seconds

    Returns:
        True if healthy, False otherwise
    """
    from a0.client.api import AgentZeroClient

    async def _check() -> bool:
        client = AgentZeroClient(url, api_key, timeout=timeout)
        try:
            return await client.health()
        except Exception:
            return False
        finally:
            await client.close()

    return asyncio.run(_check())


def _prompt_auto_start(console: Console) -> bool:
    """Prompt user to start Agent Zero."""
    console.print()
    console.print("[yellow]Agent Zero is not running.[/yellow]")
    return Confirm.ask("Start it now?", default=True)


def _start_docker_with_progress(
    console: Console,
    compose_file: Path | None = None,
) -> bool:
    """Start Agent Zero Docker container with progress display.

    Returns:
        True if started successfully, False otherwise.
    """
    from a0.utils.docker import start_agent_zero

    console.print()
    with console.status("[bold blue]Starting Agent Zero..."):
        try:
            start_agent_zero(detach=True, compose_file=compose_file)
            return True
        except Exception as e:
            console.print(f"[red]Failed to start: {e}[/red]")
            return False


def _wait_for_ready(
    console: Console,
    url: str,
    api_key: str | None,
    timeout: float = 30.0,
) -> bool:
    """Poll until Agent Zero is ready.

    Returns:
        True if ready within timeout, False otherwise.
    """
    import time

    start = time.time()
    with console.status("[bold blue]Waiting for Agent Zero to be ready..."):
        while time.time() - start < timeout:
            if check_health(url, api_key, timeout=1.0):
                console.print("[green]Agent Zero is ready![/green]")
                return True
            time.sleep(2.0)

    console.print("[red]Timed out waiting for Agent Zero.[/red]")
    return False


def launch_repl(
    url: str,
    api_key: str | None,
    project: str | None,
    compose_file: Path | None = None,
) -> None:
    """Launch the REPL interface with real-time progress.

    Args:
        url: Agent Zero URL
        api_key: Optional API key
        project: Optional project name
        compose_file: Optional Docker compose file path
    """
    console = Console()

    # Check if Agent Zero is running
    if not check_health(url, api_key):
        if _prompt_auto_start(console):
            if not _start_docker_with_progress(console, compose_file):
                return
            if not _wait_for_ready(console, url, api_key):
                return
        else:
            return

    from rich.live import Live
    from rich.spinner import Spinner
    from rich.markdown import Markdown
    from rich.text import Text
    from a0.client.api import AgentZeroClient

    # Custom markdown with left-aligned headers
    class LeftAlignedMarkdown(Markdown):
        """Markdown with left-aligned headers."""
        def __init__(self, markup: str, **kwargs) -> None:
            super().__init__(markup, justify="left", **kwargs)

    async def _repl() -> None:
        client = AgentZeroClient(url, api_key)
        ctx_id = ""

        console.print("[dim]Type /exit or Ctrl-D to quit[/dim]")
        console.print()

        try:
            while True:
                try:
                    user_input = console.input("[bold cyan]>[/bold cyan] ")
                except (EOFError, KeyboardInterrupt):
                    console.print()
                    break

                stripped = user_input.strip()
                if not stripped:
                    continue
                if stripped in ("/exit", "/quit", "/menu"):
                    break

                # Send message with real-time progress display
                try:
                    response_task = asyncio.create_task(
                        client.send_message(
                            message=user_input,
                            context_id=ctx_id,
                            project_name=project,
                        )
                    )

                    # Poll for real-time progress while waiting
                    status_text = "Thinking..."
                    last_log_count = 0

                    with Live(
                        Spinner("dots", text=Text(status_text, style="cyan")),
                        console=console,
                        refresh_per_second=10,
                        transient=True,
                    ) as live:
                        while not response_task.done():
                            # Try to get current logs if we have a context
                            if ctx_id:
                                try:
                                    logs = await client.get_logs(ctx_id, length=50)
                                    if logs.log.items:
                                        new_items = logs.log.items[last_log_count:]
                                        for item in new_items:
                                            log_type = item.get("type", "")
                                            heading = item.get("heading", "")
                                            if log_type == "agent":
                                                status_text = f"Thinking: {heading[:40]}..." if heading else "Thinking..."
                                            elif log_type == "tool":
                                                tool = item.get("kvps", {}).get("tool_name", "tool")
                                                status_text = f"Using {tool}..."
                                            elif log_type == "code_exe":
                                                status_text = "Running code..."
                                            elif log_type == "browser":
                                                status_text = "Browsing web..."
                                            elif log_type == "progress":
                                                status_text = heading or "Working..."
                                        last_log_count = len(logs.log.items)
                                        live.update(Spinner("dots", text=Text(status_text, style="cyan")))
                                except Exception:
                                    pass  # Ignore polling errors

                            await asyncio.sleep(0.3)

                    response = await response_task
                    ctx_id = response.context_id

                    # Print response
                    console.print()
                    console.print(LeftAlignedMarkdown(response.response))
                    console.print()

                except Exception as e:
                    err_msg = str(e)
                    if "401" in err_msg or "Unauthorized" in err_msg:
                        console.print("[red]Authentication required.[/red]")
                        console.print("[dim]Set API key: a0 config --set api_key=YOUR_KEY[/dim]")
                    else:
                        console.print(f"[red]Error: {err_msg}[/red]")
                    console.print()

        finally:
            await client.close()

    asyncio.run(_repl())


def _print_log(console: Console, log: dict) -> None:
    """Print a log item to the console."""
    prefix_map = {
        "agent": "[blue]GEN[/blue]",
        "tool": "[yellow]USE[/yellow]",
        "code_exe": "[magenta]RUN[/magenta]",
        "browser": "[cyan]BRW[/cyan]",
        "response": "[green]RSP[/green]",
        "error": "[red]ERR[/red]",
        "warning": "[yellow]WRN[/yellow]",
        "progress": "[dim]...[/dim]",
        "info": "[dim]INF[/dim]",
    }
    log_type = log.get("type", "")
    prefix = prefix_map.get(log_type, f"[dim]{log_type[:3].upper()}[/dim]")
    heading = log.get("heading") or log_type
    content = (log.get("content") or "")[:200]

    console.print(f"  {prefix} {heading}")
    if content:
        console.print(f"      {content}")


def show_status(url: str, api_key: str | None) -> None:
    """Show Agent Zero connection status."""
    console = Console()
    console.print()

    if check_health(url, api_key, timeout=2.0):
        console.print(f"[green]Agent Zero is running[/green] at {url}")
    else:
        console.print(f"[red]Agent Zero is not running[/red] at {url}")

    console.print()
    console.print("[dim]Press any key to continue...[/dim]")

    # Wait for keypress
    import sys
    import tty
    import termios

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def toggle_docker(compose_file: Path | None = None) -> None:
    """Toggle Docker container state (start if stopped, stop if running)."""
    from a0.utils.docker import start_agent_zero, stop_agent_zero

    console = Console()
    console.print()

    # Check current state by trying to connect
    # We use a simple heuristic: if docker ps shows the container, it's running
    import subprocess

    result = subprocess.run(
        ["docker", "ps", "--filter", "name=agent-zero", "--format", "{{.Names}}"],
        capture_output=True,
        text=True,
    )
    is_running = "agent-zero" in result.stdout

    if is_running:
        with console.status("[bold blue]Stopping Agent Zero..."):
            try:
                stop_agent_zero()
                console.print("[green]Agent Zero stopped.[/green]")
            except Exception as e:
                console.print(f"[red]Failed to stop: {e}[/red]")
    else:
        with console.status("[bold blue]Starting Agent Zero..."):
            try:
                start_agent_zero(detach=True, compose_file=compose_file)
                console.print("[green]Agent Zero started.[/green]")
            except Exception as e:
                console.print(f"[red]Failed to start: {e}[/red]")

    console.print()
    console.print("[dim]Press any key to continue...[/dim]")

    import sys
    import tty
    import termios

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def open_settings() -> None:
    """Open the settings editor."""
    from a0.utils.config import Config

    console = Console()
    config = Config.load()

    console.print()
    console.print("[bold]Settings[/bold]")
    console.print()
    console.print(f"  Agent Zero URL:  [cyan]{config.agent_url}[/cyan]")
    console.print(f"  API Key:         [cyan]{'••••••••' if config.api_key else '(not set)'}[/cyan]")
    console.print(f"  Theme:           [cyan]{config.theme}[/cyan]")
    console.print()
    console.print("[dim]Settings editor coming soon. Edit ~/.config/a0/config.toml directly.[/dim]")
    console.print()
    console.print("[dim]Press any key to continue...[/dim]")

    import sys
    import tty
    import termios

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
