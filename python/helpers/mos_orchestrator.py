"""
MOS Orchestrator — static methods for cross-system sync jobs and event hooks.

Used by:
- Scheduled cron jobs (via mos_scheduler_init.py)
- Event hooks in existing tools (customer_lifecycle, deployment_orchestrator, etc.)

All methods are fire-and-forget safe: wrapped in try/except, never crash the caller.
"""

import os
import traceback
from typing import Any


class MOSOrchestrator:
    """Static methods for cross-system orchestration."""

    # ── Scheduled sync jobs ──────────────────────────────────────────

    @staticmethod
    async def sync_linear_to_motion() -> dict[str, Any]:
        """Sync P0/P1 Linear issues → Motion time blocks.
        Scheduled: 8am, 12pm, 5pm weekdays."""
        try:
            from instruments.custom.motion_integration.motion_manager import MotionManager
            from python.helpers import files

            db_path = files.get_abs_path("./instruments/custom/motion_integration/data/motion_integration.db")
            motion_api_key = os.getenv("MOTION_API_KEY", "")
            linear_api_key = os.getenv("LINEAR_API_KEY", "")
            workspace_id = os.getenv("MOTION_WORKSPACE_ID", "")

            try:
                from python.helpers.settings import get_settings

                s = get_settings()
                motion_api_key = s.get("motion_api_key", "") or motion_api_key
                linear_api_key = s.get("linear_api_key", "") or linear_api_key
            except Exception:
                pass

            if not all([motion_api_key, linear_api_key, workspace_id]):
                return {"skipped": True, "reason": "Missing API keys or workspace_id"}

            manager = MotionManager(db_path, api_key=motion_api_key)
            return await manager.sync_from_linear(
                workspace_id=workspace_id,
                linear_api_key=linear_api_key,
            )
        except Exception as e:
            traceback.print_exc()
            return {"error": str(e)}

    @staticmethod
    async def sync_linear_activity_to_digest() -> dict[str, Any]:
        """Fetch recent Linear changes for digest_builder.
        Scheduled: 6am daily."""
        try:
            from instruments.custom.linear_integration.linear_manager import LinearManager
            from python.helpers import files

            db_path = files.get_abs_path("./instruments/custom/linear_integration/data/linear_integration.db")
            api_key = os.getenv("LINEAR_API_KEY", "")
            try:
                from python.helpers.settings import get_settings

                api_key = get_settings().get("linear_api_key", "") or api_key
            except Exception:
                pass

            if not api_key:
                return {"skipped": True, "reason": "No LINEAR_API_KEY"}

            manager = LinearManager(db_path, api_key=api_key)
            return await manager.sync_pipeline()
        except Exception as e:
            traceback.print_exc()
            return {"error": str(e)}

    # ── Event hooks (fire-and-forget) ────────────────────────────────

    @staticmethod
    async def on_lead_captured(
        customer_name: str,
        company: str = "",
        customer_id: int | None = None,
    ) -> None:
        """Hook: customer_lifecycle.capture_lead → create Linear issue."""
        try:
            from instruments.custom.linear_integration.linear_manager import LinearManager
            from python.helpers import files

            db_path = files.get_abs_path("./instruments/custom/linear_integration/data/linear_integration.db")
            api_key = os.getenv("LINEAR_API_KEY", "")
            team_id = os.getenv("LINEAR_DEFAULT_TEAM_ID", "")
            try:
                from python.helpers.settings import get_settings

                s = get_settings()
                api_key = s.get("linear_api_key", "") or api_key
                team_id = s.get("linear_default_team_id", "") or team_id
            except Exception:
                pass

            if not api_key or not team_id:
                return

            manager = LinearManager(db_path, api_key=api_key)
            await manager.create_issue(
                title=f"New Lead: {customer_name}" + (f" ({company})" if company else ""),
                team_id=team_id,
                description=f"Lead captured via customer_lifecycle.\nCustomer ID: {customer_id}",
                priority=3,  # Medium
            )
        except Exception:
            traceback.print_exc()

    @staticmethod
    async def on_deployment_success(
        project_name: str = "",
        related_issue_ids: list[str] | None = None,
    ) -> None:
        """Hook: deployment_orchestrator success → close related Linear issues."""
        try:
            if not related_issue_ids:
                return

            from instruments.custom.linear_integration.linear_manager import LinearManager
            from python.helpers import files

            db_path = files.get_abs_path("./instruments/custom/linear_integration/data/linear_integration.db")
            api_key = os.getenv("LINEAR_API_KEY", "")
            team_id = os.getenv("LINEAR_DEFAULT_TEAM_ID", "")
            try:
                from python.helpers.settings import get_settings

                s = get_settings()
                api_key = s.get("linear_api_key", "") or api_key
                team_id = s.get("linear_default_team_id", "") or team_id
            except Exception:
                pass

            if not api_key:
                return

            manager = LinearManager(db_path, api_key=api_key)

            # Get "Done" state ID for the team
            client = manager._get_client()
            if team_id:
                states = await client.get_workflow_states(team_id)
                done_state = next(
                    (s for s in states if s.get("name", "").lower() == "done"),
                    None,
                )
                if done_state:
                    for issue_id in related_issue_ids:
                        await manager.update_issue(
                            issue_id=issue_id,
                            state_id=done_state["id"],
                        )
        except Exception:
            traceback.print_exc()
