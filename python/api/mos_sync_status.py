"""
MOS Sync Status API — sync job status across all integrations.
"""

from __future__ import annotations

import traceback

from python.helpers import files
from python.helpers.api import ApiHandler


class MOSSyncStatus(ApiHandler):
    """Shows sync job status: last run, success/fail counts, next scheduled."""

    async def process(self, input: dict, request) -> dict:
        try:
            result: dict = {
                "success": True,
                "syncs": {},
            }

            # Linear sync status
            result["syncs"]["linear"] = self._get_sync_status(
                "instruments/custom/linear_integration/data/linear_integration.db",
                "linear_integration",
            )

            # Motion sync status
            result["syncs"]["motion"] = self._get_sync_status(
                "instruments/custom/motion_integration/data/motion_integration.db",
                "motion_integration",
            )

            # Notion sync status
            result["syncs"]["notion"] = self._get_sync_status(
                "instruments/custom/notion_integration/data/notion_integration.db",
                "notion_integration",
            )

            return result

        except Exception as e:
            traceback.print_exc()
            return {"success": False, "error": str(e)}

    def _get_sync_status(self, relative_db_path: str, integration_name: str) -> dict:
        try:
            import sqlite3

            db_path = files.get_abs_path(f"./{relative_db_path}")
            conn = sqlite3.connect(db_path)

            # Last sync
            cursor = conn.execute("SELECT * FROM sync_log ORDER BY id DESC LIMIT 1")
            cols = [d[0] for d in cursor.description] if cursor.description else []
            row = cursor.fetchone()
            last_sync = dict(zip(cols, row)) if row else None

            # Success/fail counts (last 30 days)
            cursor = conn.execute(
                """
                SELECT status, COUNT(*) FROM sync_log
                WHERE started_at > datetime('now', '-30 days')
                GROUP BY status
                """
            )
            counts = {row[0]: row[1] for row in cursor.fetchall()}

            conn.close()

            return {
                "last_sync": last_sync,
                "last_30_days": counts,
                "integration": integration_name,
            }
        except Exception as e:
            return {"error": str(e), "integration": integration_name}
