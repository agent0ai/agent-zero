"""Agent Zero CLI.

Commands:
  a0                    Launch interactive menu (default)
  a0 chat "message"     Send single message
  a0 chat               Interactive REPL
  a0 start              Start Agent Zero container
  a0 stop               Stop container
  a0 status             Check status
  a0 acp                Run as ACP server (stdio)
  a0 config             Manage configuration
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Optional

import typer

app = typer.Typer(
    name="a0",
    help="Agent Zero CLI — interact with Agent Zero from your terminal",
    no_args_is_help=False,
)

_DEFAULT_URL = "http://localhost:55080"


def _resolve_config(
    url: str | None,
    api_key: str | None,
) -> tuple[str, str | None]:
    """Merge CLI flags with saved config.

    Resolution: CLI flag → env var (handled by typer) → config file → default.
    """
    from a0.utils.config import Config

    cfg = Config.load()
    resolved_url = url if url != _DEFAULT_URL else cfg.agent_url
    resolved_key = api_key if api_key is not None else cfg.api_key
    return resolved_url, resolved_key


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    project: Optional[str] = typer.Option(
        None, "-p", "--project", help="Project directory"
    ),
    url: str = typer.Option(
        _DEFAULT_URL, "-u", "--url", help="Agent Zero URL"
    ),
    api_key: Optional[str] = typer.Option(
        None,
        "-k",
        "--api-key",
        envvar="AGENT_ZERO_API_KEY",
        help="API key",
    ),
) -> None:
    """Launch Agent Zero interactive menu."""
    if ctx.invoked_subcommand is None:
        # Check if we're in a TTY - menu requires interactive input
        if not sys.stdin.isatty():
            print("Error: a0 requires an interactive terminal.")
            print("Use 'a0 chat \"message\"' for non-interactive use.")
            raise typer.Exit(1)

        from a0.banner import show_banner
        from a0.launcher import (
            run_menu,
            launch_repl,
            show_status,
            toggle_docker,
            open_settings,
        )

        resolved_url, resolved_key = _resolve_config(url, api_key)

        # Show animated banner
        show_banner()

        # Run menu loop
        while True:
            action = run_menu()

            if action is None:
                # User pressed Escape - quit
                break

            elif action == "repl":
                launch_repl(
                    url=resolved_url,
                    api_key=resolved_key,
                    project=project,
                )
                # After REPL exits, show menu again

            elif action == "status":
                show_status(resolved_url, resolved_key)
                # After status, show menu again

            elif action == "docker":
                toggle_docker()
                # After docker toggle, show menu again

            elif action == "settings":
                open_settings()
                # After settings, show menu again


@app.command()
def chat(
    message: Optional[str] = typer.Argument(None, help="Message to send (omit for interactive REPL)"),
    project: Optional[str] = typer.Option(None, "-p", "--project"),
    context: Optional[str] = typer.Option(
        None, "-c", "--context", help="Context ID to continue"
    ),
    url: str = typer.Option(
        _DEFAULT_URL, "-u", "--url", envvar="AGENT_ZERO_URL"
    ),
    api_key: Optional[str] = typer.Option(
        None, "-k", "--api-key", envvar="AGENT_ZERO_API_KEY"
    ),
    follow: bool = typer.Option(
        False, "-f", "--follow", help="Follow agent activity via polling"
    ),
) -> None:
    """Send a message to Agent Zero, or start an interactive REPL."""
    from rich.console import Console
    from rich.markdown import Markdown as RichMarkdown

    from a0.client.api import AgentZeroClient

    resolved_url, resolved_key = _resolve_config(url, api_key)
    console = Console()
    is_repl = message is None
    effective_follow = follow or is_repl  # default follow=True in REPL

    async def _follow_activity(client: AgentZeroClient, context_id: str) -> None:
        from a0.client.poller import Poller

        poller = Poller(client, interval=0.5)
        async for event in poller.stream(
            context_id,
            stop_when=lambda e: not e.progress_active and not e.logs,
        ):
            for log in event.logs:
                _print_log(console, log)

    async def _send_and_print(
        client: AgentZeroClient,
        text: str,
        context_id: str,
    ) -> str:
        response = await client.send_message(
            message=text,
            context_id=context_id,
            project_name=project,
        )
        console.print(RichMarkdown(response.response))
        if effective_follow:
            await _follow_activity(client, response.context_id)
        return response.context_id

    async def _single_shot() -> None:
        assert message is not None
        client = AgentZeroClient(resolved_url, resolved_key)
        try:
            ctx_id = await _send_and_print(client, message, context or "")
            console.print(f"\n[dim]Context: {ctx_id}[/dim]")
        finally:
            await client.close()

    async def _repl() -> None:
        client = AgentZeroClient(resolved_url, resolved_key)
        ctx_id = context or ""
        from a0.banner import show_banner

        show_banner()
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
                if stripped in ("/exit", "/quit"):
                    break

                ctx_id = await _send_and_print(client, user_input, ctx_id)
        finally:
            await client.close()

    asyncio.run(_repl() if is_repl else _single_shot())


def _print_log(console: object, log: dict) -> None:
    """Print a log item dict to the console."""
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


@app.command()
def acp(
    url: str = typer.Option(
        _DEFAULT_URL, "-u", "--url", envvar="AGENT_ZERO_URL"
    ),
    api_key: Optional[str] = typer.Option(
        None, "-k", "--api-key", envvar="AGENT_ZERO_API_KEY"
    ),
) -> None:
    """Run as ACP server over stdio.

    Use this mode to integrate Agent Zero with ACP-compatible
    clients like Zed, Toad, or Cursor.
    """
    from a0.acp.server import ACPServer

    resolved_url, resolved_key = _resolve_config(url, api_key)
    server = ACPServer(agent_url=resolved_url, api_key=resolved_key)
    asyncio.run(server.run())


@app.command()
def start(
    detach: bool = typer.Option(True, "-d", "--detach", help="Run in background"),
    compose_file: Optional[Path] = typer.Option(
        None, "-f", "--file", help="Docker compose file"
    ),
) -> None:
    """Start Agent Zero Docker container."""
    from a0.utils.docker import start_agent_zero

    start_agent_zero(detach=detach, compose_file=compose_file)


@app.command()
def stop() -> None:
    """Stop Agent Zero Docker container."""
    from a0.utils.docker import stop_agent_zero

    stop_agent_zero()


@app.command()
def status(
    url: str = typer.Option(
        _DEFAULT_URL, "-u", "--url", envvar="AGENT_ZERO_URL"
    ),
    api_key: Optional[str] = typer.Option(
        None, "-k", "--api-key", envvar="AGENT_ZERO_API_KEY"
    ),
) -> None:
    """Check Agent Zero status."""
    from rich.console import Console

    from a0.client.api import AgentZeroClient

    resolved_url, resolved_key = _resolve_config(url, api_key)
    console = Console()

    async def check() -> None:
        client = AgentZeroClient(resolved_url, resolved_key)
        try:
            ok = await client.health()
            if ok:
                console.print("[green]Agent Zero is running[/green]")
            else:
                console.print("[red]Agent Zero is not running[/red]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
        finally:
            await client.close()

    asyncio.run(check())


@app.command()
def config(
    show: bool = typer.Option(False, "--show", help="Show current config"),
    set_key: Optional[str] = typer.Option(
        None, "--set", help="Set config key=value"
    ),
) -> None:
    """Manage CLI configuration."""
    from rich.console import Console
    from rich import print_json

    from a0.utils.config import Config

    console = Console()
    cfg = Config.load()

    if show:
        print_json(data=cfg.model_dump())
    elif set_key:
        key, _, value = set_key.partition("=")
        if not hasattr(cfg, key):
            console.print(f"[red]Unknown config key: {key}[/red]")
            raise typer.Exit(1)
        setattr(cfg, key, value)
        cfg.save()
        console.print(f"[green]Set {key}={value}[/green]")
    else:
        console.print("Use --show to view config or --set key=value to update")
