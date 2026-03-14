"""
Linear Integration Tool for Agent Jumbo / MOS.

Provides 6 actions: create_issue, update_issue, search_issues,
get_project_issues, sync_pipeline, get_dashboard.
"""

import json
import os

from python.helpers import files
from python.helpers.tool import Response, Tool


class LinearIntegration(Tool):
    """Agent tool for managing Linear issues, projects, and sync."""

    def __init__(self, agent, name: str, method: str | None, args: dict, message: str, loop_data=None, **kwargs):
        super().__init__(agent, name, method, args, message, loop_data, **kwargs)

        from instruments.custom.linear_integration.linear_manager import LinearManager

        db_path = files.get_abs_path("./instruments/custom/linear_integration/data/linear_integration.db")

        # Resolve API key from settings or env
        api_key = None
        try:
            from python.helpers.settings import get_settings

            api_key = get_settings().get("linear_api_key", "")
        except Exception:
            pass
        if not api_key:
            api_key = os.getenv("LINEAR_API_KEY", "")

        self.manager = LinearManager(db_path, api_key=api_key or None)

    async def execute(self, **kwargs):
        action = (self.args.get("action") or "").lower()

        handlers = {
            "create_issue": self._create_issue,
            "update_issue": self._update_issue,
            "search_issues": self._search_issues,
            "get_project_issues": self._get_project_issues,
            "sync_pipeline": self._sync_pipeline,
            "get_dashboard": self._get_dashboard,
        }

        handler = handlers.get(action)
        if not handler:
            return Response(
                message=f"Unknown action: {action}. Available: {', '.join(handlers.keys())}",
                break_loop=False,
            )
        return await handler()

    async def _create_issue(self):
        team_id = self.args.get("team_id") or self._get_default_team_id()
        if not team_id:
            return Response(
                message="team_id is required. Set linear_default_team_id in settings or pass team_id.",
                break_loop=False,
            )
        result = await self.manager.create_issue(
            title=self.args.get("title", ""),
            team_id=team_id,
            description=self.args.get("description", ""),
            priority=int(self.args.get("priority", 0)),
            label_ids=self.args.get("label_ids"),
            project_id=self.args.get("project_id"),
            state_id=self.args.get("state_id"),
        )
        return Response(message=self._fmt(result, "Issue Created"), break_loop=False)

    async def _update_issue(self):
        issue_id = self.args.get("issue_id")
        if not issue_id:
            return Response(message="issue_id is required.", break_loop=False)
        result = await self.manager.update_issue(
            issue_id=issue_id,
            title=self.args.get("title"),
            description=self.args.get("description"),
            state_id=self.args.get("state_id"),
            priority=int(self.args["priority"]) if self.args.get("priority") is not None else None,
            label_ids=self.args.get("label_ids"),
        )
        return Response(message=self._fmt(result, "Issue Updated"), break_loop=False)

    async def _search_issues(self):
        query = self.args.get("query", "")
        if not query:
            return Response(message="query is required.", break_loop=False)
        issues = await self.manager.search_issues(
            query=query,
            team_id=self.args.get("team_id"),
            limit=int(self.args.get("limit", 25)),
            use_cache=self.args.get("use_cache", False),
        )
        return Response(
            message=self._fmt({"issues": issues, "count": len(issues)}, "Search Results"),
            break_loop=False,
        )

    async def _get_project_issues(self):
        project_id = self.args.get("project_id")
        if not project_id:
            return Response(message="project_id is required.", break_loop=False)
        issues = await self.manager.get_project_issues(
            project_id=project_id,
            limit=int(self.args.get("limit", 50)),
            use_cache=self.args.get("use_cache", False),
        )
        return Response(
            message=self._fmt({"issues": issues, "count": len(issues)}, "Project Issues"),
            break_loop=False,
        )

    async def _sync_pipeline(self):
        team_id = self.args.get("team_id") or self._get_default_team_id()
        result = await self.manager.sync_pipeline(team_id=team_id)
        return Response(message=self._fmt(result, "Sync Pipeline"), break_loop=False)

    async def _get_dashboard(self):
        data = self.manager.get_dashboard()
        return Response(message=self._fmt(data, "Linear Dashboard"), break_loop=False)

    # ── Helpers ──────────────────────────────────────────────────────

    def _get_default_team_id(self) -> str:
        try:
            from python.helpers.settings import get_settings

            return get_settings().get("linear_default_team_id", "")
        except Exception:
            return os.getenv("LINEAR_DEFAULT_TEAM_ID", "")

    def _fmt(self, result: dict, title: str) -> str:
        if not result:
            return f"**{title}**: No data"
        if "error" in result:
            return f"**{title} - Error**: {result['error']}"
        return f"**{title}**:\n```json\n{json.dumps(result, indent=2, default=str)}\n```"
