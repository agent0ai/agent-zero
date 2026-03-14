"""
Linear Dashboard API — provides cached Linear data for UI dashboards.
"""

from __future__ import annotations

import os
import traceback

from python.helpers import files
from python.helpers.api import ApiHandler


class LinearDashboard(ApiHandler):
    """API endpoint for Linear dashboard data."""

    async def process(self, input: dict, request) -> dict:
        try:
            from instruments.custom.linear_integration.linear_manager import LinearManager

            db_path = files.get_abs_path("./instruments/custom/linear_integration/data/linear_integration.db")

            api_key = None
            try:
                from python.helpers.settings import get_settings

                api_key = get_settings().get("linear_api_key", "")
            except Exception:
                pass
            if not api_key:
                api_key = os.getenv("LINEAR_API_KEY", "")

            manager = LinearManager(db_path, api_key=api_key or None)

            action = input.get("action", "dashboard")

            if action == "dashboard":
                data = manager.get_dashboard()
                return {"success": True, **data}

            if action == "sync":
                team_id = input.get("team_id", "")
                if not team_id:
                    try:
                        from python.helpers.settings import get_settings

                        team_id = get_settings().get("linear_default_team_id", "")
                    except Exception:
                        pass
                result = await manager.sync_pipeline(team_id=team_id or None)
                return {"success": result.get("success", False), **result}

            if action == "issues":
                project_id = input.get("project_id")
                issues = manager.db.get_issues(
                    project_id=project_id,
                    state_name=input.get("state"),
                    limit=int(input.get("limit", 50)),
                )
                return {"success": True, "issues": issues, "count": len(issues)}

            if action == "projects":
                projects = manager.db.get_projects()
                return {"success": True, "projects": projects, "count": len(projects)}

            return {"success": False, "error": f"Unknown action: {action}"}

        except Exception as e:
            traceback.print_exc()
            return {"success": False, "error": str(e)}
