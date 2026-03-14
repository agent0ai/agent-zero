"""
MOS Dashboard API — aggregated view of Linear, Motion, and pipeline health.
"""

from __future__ import annotations

import traceback

from python.helpers import files
from python.helpers.api import ApiHandler


class MOSDashboard(ApiHandler):
    """Unified MOS dashboard combining data from all integration caches."""

    async def process(self, input: dict, request) -> dict:
        try:
            result: dict = {
                "success": True,
                "linear": {},
                "motion": {},
                "pipeline": {},
            }

            # Linear data
            if input.get("include_linear", True):
                result["linear"] = self._get_linear_data()

            # Motion data
            if input.get("include_motion", True):
                result["motion"] = self._get_motion_data()

            # Pipeline health (from customer_lifecycle)
            if input.get("include_pipeline", True):
                result["pipeline"] = self._get_pipeline_data()

            return result

        except Exception as e:
            traceback.print_exc()
            return {"success": False, "error": str(e)}

    def _get_linear_data(self) -> dict:
        try:
            from instruments.custom.linear_integration.linear_db import LinearDatabase

            db_path = files.get_abs_path("./instruments/custom/linear_integration/data/linear_integration.db")
            db = LinearDatabase(db_path)
            return db.get_dashboard_data()
        except Exception as e:
            return {"error": str(e)}

    def _get_motion_data(self) -> dict:
        try:
            from instruments.custom.motion_integration.motion_db import MotionDatabase

            db_path = files.get_abs_path("./instruments/custom/motion_integration/data/motion_integration.db")
            db = MotionDatabase(db_path)
            tasks = db.get_tasks(limit=20)
            mappings = db.get_all_mappings()
            last_sync = db.get_last_sync("linear_sync")
            return {
                "recent_tasks": tasks,
                "task_count": len(tasks),
                "linear_mappings": len(mappings),
                "last_sync": last_sync,
            }
        except Exception as e:
            return {"error": str(e)}

    def _get_pipeline_data(self) -> dict:
        try:
            from instruments.custom.customer_lifecycle.lifecycle_db import (
                CustomerLifecycleDatabase,
            )

            db_path = files.get_abs_path("./instruments/custom/customer_lifecycle/data/customer_lifecycle.db")
            db = CustomerLifecycleDatabase(db_path)
            return db.get_pipeline_summary()
        except Exception as e:
            return {"error": str(e)}
