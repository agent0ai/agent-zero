"""
Motion Integration Tool for Agent Jumbo / MOS.

4 actions: create_task, list_tasks, get_schedule, sync_from_linear.
"""

import json
import os

from python.helpers import files
from python.helpers.tool import Response, Tool


class MotionIntegration(Tool):
    """Agent tool for managing Motion tasks and syncing from Linear."""

    def __init__(self, agent, name: str, method: str | None, args: dict, message: str, loop_data=None, **kwargs):
        super().__init__(agent, name, method, args, message, loop_data, **kwargs)

        from instruments.custom.motion_integration.motion_manager import MotionManager

        db_path = files.get_abs_path("./instruments/custom/motion_integration/data/motion_integration.db")

        api_key = None
        try:
            from python.helpers.settings import get_settings

            api_key = get_settings().get("motion_api_key", "")
        except Exception:
            pass
        if not api_key:
            api_key = os.getenv("MOTION_API_KEY", "")

        self.manager = MotionManager(db_path, api_key=api_key or None)

    async def execute(self, **kwargs):
        action = (self.args.get("action") or "").lower()

        handlers = {
            "create_task": self._create_task,
            "list_tasks": self._list_tasks,
            "get_schedule": self._get_schedule,
            "sync_from_linear": self._sync_from_linear,
        }

        handler = handlers.get(action)
        if not handler:
            return Response(
                message=f"Unknown action: {action}. Available: {', '.join(handlers.keys())}",
                break_loop=False,
            )
        return await handler()

    async def _create_task(self):
        workspace_id = self.args.get("workspace_id", "")
        if not workspace_id:
            return Response(message="workspace_id is required.", break_loop=False)
        result = await self.manager.create_task(
            name=self.args.get("name", ""),
            workspace_id=workspace_id,
            description=self.args.get("description", ""),
            priority=self.args.get("priority", "MEDIUM"),
            duration=int(self.args.get("duration", 30)),
            deadline=self.args.get("deadline"),
            project_id=self.args.get("project_id"),
            labels=self.args.get("labels"),
        )
        return Response(message=self._fmt(result, "Motion Task Created"), break_loop=False)

    async def _list_tasks(self):
        workspace_id = self.args.get("workspace_id", "")
        if not workspace_id:
            return Response(message="workspace_id is required.", break_loop=False)
        tasks = await self.manager.list_tasks(
            workspace_id=workspace_id,
            project_id=self.args.get("project_id"),
            status=self.args.get("status"),
            use_cache=self.args.get("use_cache", False),
        )
        return Response(
            message=self._fmt({"tasks": tasks, "count": len(tasks)}, "Motion Tasks"),
            break_loop=False,
        )

    async def _get_schedule(self):
        workspace_id = self.args.get("workspace_id", "")
        if not workspace_id:
            return Response(message="workspace_id is required.", break_loop=False)
        tasks = await self.manager.get_schedule(workspace_id=workspace_id)
        return Response(
            message=self._fmt({"schedule": tasks, "count": len(tasks)}, "Motion Schedule"),
            break_loop=False,
        )

    async def _sync_from_linear(self):
        workspace_id = self.args.get("workspace_id", "")
        if not workspace_id:
            return Response(message="workspace_id is required.", break_loop=False)

        linear_api_key = None
        linear_team_id = None
        try:
            from python.helpers.settings import get_settings

            settings = get_settings()
            linear_api_key = settings.get("linear_api_key", "")
            linear_team_id = self.args.get("linear_team_id") or settings.get("linear_default_team_id", "")
        except Exception:
            pass
        if not linear_api_key:
            linear_api_key = os.getenv("LINEAR_API_KEY", "")

        result = await self.manager.sync_from_linear(
            workspace_id=workspace_id,
            linear_api_key=linear_api_key or None,
            linear_team_id=linear_team_id or None,
        )
        return Response(message=self._fmt(result, "Linear → Motion Sync"), break_loop=False)

    def _fmt(self, result: dict, title: str) -> str:
        if not result:
            return f"**{title}**: No data"
        if "error" in result:
            return f"**{title} - Error**: {result['error']}"
        return f"**{title}**:\n```json\n{json.dumps(result, indent=2, default=str)}\n```"
