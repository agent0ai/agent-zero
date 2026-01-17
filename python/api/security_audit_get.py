import builtins
import contextlib
import json
import sqlite3

from python.helpers import files
from python.helpers.api import ApiHandler, Request, Response


class security_audit_get(ApiHandler):
    """API handler to retrieve security audit logs."""

    async def process(self, input: dict, request: Request) -> dict | Response:
        try:
            db_path = files.get_abs_path("./instruments/custom/workflow_engine/data/workflow.db")
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Get latest 100 logs
            limit = input.get("limit", 100)
            cursor.execute("""
                SELECT id, timestamp, event_type, status, user_id, ip_address, device_info, details
                FROM security_audit_log
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))

            rows = cursor.fetchall()
            logs = []
            for row in rows:
                log = dict(row)
                if log["details"]:
                    with contextlib.suppress(builtins.BaseException):
                        log["details"] = json.loads(log["details"])
                logs.append(log)

            conn.close()

            return {
                "success": True,
                "logs": logs
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
