from __future__ import annotations

import asyncio
from typing import Any

from helpers.api import ApiHandler, Request
from plugins._sandboxing.helpers.images import image_info_dict
from plugins._sandboxing.helpers.manager import SandboxError, sandbox_info_dict
from plugins._sandboxing.helpers.runtime import defaults, get_manager


class Sandboxes(ApiHandler):
    async def process(self, input: dict[str, Any], request: Request) -> dict[str, Any]:
        action = str(input.get("action") or "list").strip().lower()
        try:
            manager = get_manager()
            if action == "list":
                sandboxes = await asyncio.to_thread(manager.list)
                images = await asyncio.to_thread(manager.list_images)
                default_name, default_type, default_network = defaults()
                return {
                    "ok": True,
                    "sandboxes": [sandbox_info_dict(item) for item in sandboxes],
                    "images": [image_info_dict(item) for item in images],
                    "defaults": {
                        "name": default_name,
                        "sandbox_type": default_type,
                        "network": default_network,
                        "image": manager.config.default_image,
                    },
                    "image_cleanup_days": manager.images.config.cleanup_days,
                    "shared_dir": str(manager.config.shared_dir),
                }
            if action == "doctor":
                diagnostics = await asyncio.to_thread(manager.doctor)
                return {
                    "ok": not any(line.startswith("ERROR:") for line in diagnostics),
                    "diagnostics": diagnostics,
                }
            name = str(input.get("name") or "").strip()
            if action == "create":
                default_name, default_type, default_network = defaults()
                item = await asyncio.to_thread(
                    manager.create,
                    name or default_name,
                    sandbox_type=str(input.get("sandbox_type") or default_type),
                    network=str(input.get("network") or default_network),
                    image=str(input.get("image") or manager.config.default_image),
                    mounts=input.get("mounts") or [],
                )
            elif action in {"start", "wake"}:
                item = await asyncio.to_thread(manager.start, name)
            elif action in {"stop", "sleep"}:
                item = await asyncio.to_thread(manager.stop, name)
            elif action == "save":
                item = await asyncio.to_thread(manager.save, name)
            elif action == "inspect":
                item = await asyncio.to_thread(manager.inspect, name)
            elif action == "delete":
                if input.get("confirm") is not True:
                    return {"ok": False, "error": "delete requires confirm=true"}
                removed = await asyncio.to_thread(manager.delete, name)
                return {"ok": True, "name": name, "deleted": removed}
            elif action == "cleanup":
                deleted = await asyncio.to_thread(manager.cleanup_expired)
                return {"ok": True, "deleted": deleted}
            elif action in {"pull_image", "refresh_image"}:
                image = str(input.get("image") or manager.config.default_image).strip()
                value = await asyncio.to_thread(manager.pull_image, image)
                return {"ok": True, "image": image_info_dict(value)}
            elif action == "inspect_image":
                identifier = str(input.get("image") or input.get("digest") or "").strip()
                value = await asyncio.to_thread(manager.inspect_image, identifier)
                return {"ok": True, "image": image_info_dict(value)}
            elif action == "delete_image":
                if input.get("confirm") is not True:
                    return {"ok": False, "error": "delete_image requires confirm=true"}
                identifier = str(input.get("digest") or input.get("image") or "").strip()
                removed = await asyncio.to_thread(manager.delete_image, identifier)
                return {"ok": True, "image": identifier, "deleted": removed}
            elif action == "cleanup_images":
                deleted = await asyncio.to_thread(manager.cleanup_images)
                return {"ok": True, "deleted_images": deleted}
            else:
                return {"ok": False, "error": f"Unknown action: {action}"}
            return {"ok": True, "sandbox": sandbox_info_dict(item)}
        except (SandboxError, ValueError) as exc:
            return {"ok": False, "error": str(exc)}
