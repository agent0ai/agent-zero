"""Docker compose helpers for Agent Zero."""

from __future__ import annotations

import subprocess
from pathlib import Path

from rich.console import Console

console = Console()


def _find_compose_file() -> Path | None:
    """Find docker-compose file in common locations."""
    import os

    candidates = [
        # Current directory
        Path.cwd() / "docker-compose.yml",
        Path.cwd() / "docker-compose.yaml",
        Path.cwd() / "docker" / "run" / "docker-compose.yml",
    ]

    # Check AGENT_ZERO_DIR env var
    az_dir = os.environ.get("AGENT_ZERO_DIR")
    if az_dir:
        az_path = Path(az_dir)
        candidates.append(az_path / "docker" / "run" / "docker-compose.yml")
        candidates.append(az_path / "docker-compose.yml")

    # Common install locations
    candidates.extend([
        Path.home() / "agent-zero-dev" / "docker" / "run" / "docker-compose.yml",
        Path.home() / "agent-zero" / "docker" / "run" / "docker-compose.yml",
    ])

    for path in candidates:
        if path.exists():
            return path
    return None


def start_agent_zero(
    detach: bool = True,
    compose_file: Path | None = None,
) -> None:
    """Start Agent Zero via docker compose."""
    compose_file = compose_file or _find_compose_file()
    if not compose_file:
        console.print("[red]No docker-compose file found.[/red]")
        console.print("Provide one with --file or run from the agent-zero directory.")
        return

    cmd = ["docker", "compose", "-f", str(compose_file), "up"]
    if detach:
        cmd.append("-d")

    console.print(f"Starting Agent Zero from {compose_file}...")
    result = subprocess.run(cmd, capture_output=not detach)
    if result.returncode == 0 and detach:
        console.print("[green]Agent Zero started.[/green]")
    elif result.returncode != 0:
        console.print(f"[red]Failed to start (exit {result.returncode}).[/red]")


def stop_agent_zero(compose_file: Path | None = None) -> None:
    """Stop Agent Zero via docker compose."""
    compose_file = compose_file or _find_compose_file()
    if not compose_file:
        console.print("[red]No docker-compose file found.[/red]")
        return

    cmd = ["docker", "compose", "-f", str(compose_file), "down"]
    console.print("Stopping Agent Zero...")
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode == 0:
        console.print("[green]Agent Zero stopped.[/green]")
    else:
        console.print(f"[red]Failed to stop (exit {result.returncode}).[/red]")
