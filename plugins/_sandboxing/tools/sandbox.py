from __future__ import annotations

import asyncio
import json
from typing import Any

from helpers import projects
from helpers.tool import Response, Tool
from plugins._sandboxing.helpers.images import image_info_dict
from plugins._sandboxing.helpers.manager import SandboxError, sandbox_info_dict
from plugins._sandboxing.helpers.runtime import defaults, get_manager


class Sandbox(Tool):
    async def execute(
        self,
        action: str = "list",
        name: str = "",
        sandbox_type: str = "",
        network: str = "",
        image: str = "",
        mounts: list[dict[str, Any]] | None = None,
        confirm: bool = False,
        **kwargs: Any,
    ) -> Response:
        action = str(action or self.args.get("action") or "list").strip().lower()
        name = str(name or self.args.get("name") or "").strip()
        image = str(image or self.args.get("image") or "").strip()
        try:
            manager = get_manager(agent=self.agent)
            if action in {"list", "ls"}:
                values = await asyncio.to_thread(manager.list)
                payload = [sandbox_info_dict(value) for value in values]
                return self._json({"sandboxes": payload})
            if action in {"images", "list_images"}:
                values = await asyncio.to_thread(manager.list_images)
                return self._json(
                    {"images": [image_info_dict(value) for value in values]}
                )
            if action in {"inspect_image", "image_status"}:
                value = await asyncio.to_thread(
                    manager.inspect_image, image or name
                )
                return self._json(image_info_dict(value))
            if action in {"pull_image", "refresh_image"}:
                value = await asyncio.to_thread(manager.pull_image, image or name)
                return self._json(image_info_dict(value))
            if action in {"inspect", "status", "get"}:
                return self._json(
                    sandbox_info_dict(await asyncio.to_thread(manager.inspect, name))
                )
            if action == "doctor":
                diagnostics = await asyncio.to_thread(manager.doctor)
                return self._json(
                    {
                        "ok": not any(line.startswith("ERROR:") for line in diagnostics),
                        "diagnostics": diagnostics,
                    }
                )
            if action in {"create", "new"}:
                configured_name, configured_type, configured_network = defaults(
                    agent=self.agent
                )
                if not name:
                    name = configured_name
                sandbox_type = str(sandbox_type or configured_type)
                network = str(network or configured_network)
                info = await asyncio.to_thread(
                    manager.create,
                    name,
                    network=network,
                    sandbox_type=sandbox_type,
                    image=image,
                    mounts=self._mounts(mounts),
                    ownership=self._ownership(),
                )
                return self._json(sandbox_info_dict(info))
            if action in {"start", "wake"}:
                return self._json(
                    sandbox_info_dict(await asyncio.to_thread(manager.start, name))
                )
            if action in {"stop", "sleep"}:
                return self._json(
                    sandbox_info_dict(await asyncio.to_thread(manager.stop, name))
                )
            if action in {"save", "snapshot"}:
                return self._json(
                    sandbox_info_dict(await asyncio.to_thread(manager.save, name))
                )
            if action == "cleanup":
                deleted = await asyncio.to_thread(manager.cleanup_expired)
                return self._json({"deleted": deleted})
            if action == "cleanup_images":
                deleted = await asyncio.to_thread(manager.cleanup_images)
                return self._json({"deleted_images": deleted})
            if action in {"delete_image", "remove_image"}:
                if not confirm:
                    return Response(
                        message="Deleting a cached image is destructive. Repeat with confirm=true.",
                        break_loop=False,
                    )
                identifier = image or name
                removed = await asyncio.to_thread(manager.delete_image, identifier)
                return self._json({"image": identifier, "deleted": removed})
            if action in {"delete", "remove"}:
                if not confirm:
                    return Response(
                        message="Deleting a sandbox is destructive. Repeat with confirm=true.",
                        break_loop=False,
                    )
                removed = await asyncio.to_thread(manager.delete, name)
                return self._json({"name": name, "deleted": removed})
        except (SandboxError, ValueError) as exc:
            return Response(message=f"Sandbox error: {exc}", break_loop=False)
        return Response(
            message=(
                "Unknown action. Use list, inspect, doctor, create, start, stop, "
                "save, cleanup, delete, images, pull_image, inspect_image, "
                "cleanup_images, or delete_image."
            ),
            break_loop=False,
        )

    def _ownership(self) -> dict[str, str | None]:
        context = getattr(self.agent, "context", None)
        return {
            "chat_id": str(getattr(context, "id", "") or "") or None,
            "project_id": projects.get_context_project_name(context) if context else None,
            "agent_id": str(getattr(self.agent, "agent_name", "") or "") or None,
        }

    @staticmethod
    def _mounts(raw: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
        return list(raw or [])

    @staticmethod
    def _json(value: Any) -> Response:
        return Response(
            message=json.dumps(value, indent=2, ensure_ascii=False, default=str),
            break_loop=False,
        )
