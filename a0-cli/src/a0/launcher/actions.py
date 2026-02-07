"""Action handlers for the launcher menu.

Each action corresponds to a menu option: TUI, REPL, Status, Docker, Settings.
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


def launch_tui(
    url: str,
    api_key: str | None,
    project: str | None,
    cwd: str,
    compose_file: Path | None = None,
) -> bool:
    """Launch the TUI interface.

    Args:
        url: Agent Zero URL
        api_key: Optional API key
        project: Optional project name
        cwd: Current working directory
        compose_file: Optional Docker compose file path

    Returns:
        True if user wants to return to menu, False to quit entirely.
    """
    console = Console()

    # Check if Agent Zero is running
    if not check_health(url, api_key):
        if _prompt_auto_start(console):
            if not _start_docker_with_progress(console, compose_file):
                return True  # Return to menu
            if not _wait_for_ready(console, url, api_key):
                return True  # Return to menu
        else:
            return True  # Return to menu

    # Launch TUI
    from a0.tui.app import AgentZeroTUI

    tui = AgentZeroTUI(
        agent_url=url,
        api_key=api_key,
        project=project,
        cwd=cwd,
    )
    result = tui.run()

    # Return True if user wants to go back to menu
    return result == "menu"


def launch_repl(
    url: str,
    api_key: str | None,
    project: str | None,
    compose_file: Path | None = None,
) -> None:
    """Launch the REPL interface.

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

    # Launch REPL (reuse existing implementation from cli.py)
    from rich.markdown import Markdown as RichMarkdown
    from a0.client.api import AgentZeroClient
    from a0.client.poller import Poller

    async def _repl() -> None:
        client = AgentZeroClient(url, api_key)
        ctx_id = ""

        console.print("[dim]Type /exit or Ctrl-D to quit[/dim]")
        try:
            while True:
                try:
                    user_input = console.input("[bold]> [/bold]")
                except (EOFError, KeyboardInterrupt):
                    console.print()
                    break

                stripped = user_input.strip()
                if not stripped:
                    continue
                if stripped in ("/exit", "/quit", "/menu"):
                    break

                # Send message
                response = await client.send_message(
                    message=user_input,
                    context_id=ctx_id,
                    project_name=project,
                )
                console.print(RichMarkdown(response.response))
                ctx_id = response.context_id

                # Follow activity
                poller = Poller(client, interval=0.5)
                async for event in poller.stream(
                    ctx_id,
                    stop_when=lambda e: not e.progress_active and not e.logs,
                ):
                    for log in event.logs:
                        _print_log(console, log)

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
