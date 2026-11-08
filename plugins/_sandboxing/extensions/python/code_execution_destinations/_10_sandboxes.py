from __future__ import annotations

import asyncio

from helpers.extension import Extension
from plugins._code_execution.helpers.destinations import ExecutionDestination
from plugins._sandboxing.helpers.runtime import defaults, get_manager


class IncludeSandboxDestinations(Extension):
    async def execute(
        self, destinations: list[ExecutionDestination], **kwargs
    ) -> None:
        default_name, _, _ = defaults(agent=self.agent)
        destinations.insert(
            0,
            ExecutionDestination(
                id="default",
                kind="sandbox",
                target=default_name,
                label=f"Default sandbox ({default_name})",
                description="Default isolated execution destination; created or woken automatically.",
                status="default",
            ),
        )
        try:
            manager = get_manager(agent=self.agent)
            sandboxes = await asyncio.to_thread(manager.list)
        except Exception:
            return
        reserved = {"default", "local", "host"}
        for sandbox in sandboxes:
            if sandbox.service:
                continue
            destination_id = (
                f"sandbox:{sandbox.name}" if sandbox.name in reserved else sandbox.name
            )
            if sandbox.name == default_name:
                continue
            destinations.append(
                ExecutionDestination(
                    id=destination_id,
                    kind="sandbox",
                    target=sandbox.name,
                    label=f"Sandbox {sandbox.name}",
                    description=(
                        f"{sandbox.sandbox_type} gVisor sandbox; network={sandbox.network}."
                    ),
                    status=sandbox.status,
                )
            )
