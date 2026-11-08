from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from helpers.extension import call_extensions_async


DestinationKind = Literal["local", "sandbox", "host"]


@dataclass(frozen=True, slots=True)
class ExecutionDestination:
    id: str
    kind: DestinationKind
    label: str
    description: str
    target: str = ""
    status: str = "available"


async def get_code_execution_destinations(agent: Any) -> list[ExecutionDestination]:
    destinations = [
        ExecutionDestination(
            id="local",
            kind="local",
            label="Agent Zero system",
            description="The operating system running Agent Zero; use only for Agent Zero itself or its core files.",
        )
    ]
    await call_extensions_async(
        "code_execution_destinations",
        agent=agent,
        destinations=destinations,
    )
    unique: dict[str, ExecutionDestination] = {}
    for destination in destinations:
        if destination.id and destination.id not in unique:
            unique[destination.id] = destination
    return list(unique.values())


async def resolve_code_execution_destination(
    agent: Any, requested: str
) -> ExecutionDestination:
    requested = str(requested or "default").strip() or "default"
    destinations = await get_code_execution_destinations(agent)
    for destination in destinations:
        if destination.id == requested:
            return destination

    if requested in {"local", "host", "default"}:
        raise ValueError(f"Code execution destination is not currently available: {requested}")

    # Named sandboxes are intentionally lazy: a missing one is created when its
    # first shell connects. The sandbox plugin still validates the exact name.
    try:
        from plugins._sandboxing.helpers.manager import validate_name

        sandbox_name = requested.split(":", 1)[1] if requested.startswith("sandbox:") else requested
        validate_name(sandbox_name)
    except (ImportError, IndexError, ValueError, RuntimeError) as exc:
        raise ValueError(f"Unknown code execution destination: {requested}") from exc
    return ExecutionDestination(
        id=requested,
        kind="sandbox",
        target=sandbox_name,
        label=f"Sandbox {sandbox_name}",
        description="A gVisor sandbox that will be created or woken on first use.",
        status="missing",
    )
