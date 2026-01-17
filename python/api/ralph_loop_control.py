"""
API endpoint for Ralph Loop control operations.
Handles pause, resume, cancel, and detail retrieval.
"""

import os

from python.helpers import files
from python.helpers.api import ApiHandler, Request, Response


class RalphLoopControl(ApiHandler):
    """API handler for Ralph Loop control operations."""

    async def process(self, input: dict, request: Request) -> dict | Response:
        try:
            # Import the Ralph Loop manager
            from instruments.custom.ralph_loop.ralph_manager import RalphLoopManager

            # Get database path
            db_path = files.get_abs_path(
                "./instruments/custom/ralph_loop/data/ralph_loop.db"
            )

            # Ensure data directory exists
            data_dir = os.path.dirname(db_path)
            if not os.path.exists(data_dir):
                os.makedirs(data_dir, exist_ok=True)

            # Initialize manager
            manager = RalphLoopManager(db_path)

            # Get action from input
            action = input.get("action", "").lower()
            loop_id = input.get("loop_id")

            if action == "pause":
                if not loop_id:
                    return {"success": False, "error": "loop_id is required"}
                result = manager.pause_loop(loop_id)
                if "error" in result:
                    return {"success": False, "error": result["error"]}
                return {"success": True, "result": result}

            elif action == "resume":
                if not loop_id:
                    return {"success": False, "error": "loop_id is required"}
                result = manager.resume_loop(loop_id)
                if "error" in result:
                    return {"success": False, "error": result["error"]}
                return {"success": True, "result": result}

            elif action == "cancel":
                if not loop_id:
                    return {"success": False, "error": "loop_id is required"}
                reason = input.get("reason", "Cancelled via UI")
                result = manager.cancel_loop(loop_id, reason=reason)
                if "error" in result:
                    return {"success": False, "error": result["error"]}
                return {"success": True, "result": result}

            elif action == "get_details":
                if not loop_id:
                    return {"success": False, "error": "loop_id is required"}
                result = manager.get_status(loop_id)
                if "error" in result:
                    return {"success": False, "error": result["error"]}
                return {"success": True, "loop": result}

            elif action == "get_history":
                if not loop_id:
                    return {"success": False, "error": "loop_id is required"}
                iterations = manager.get_iteration_history(loop_id)
                loop = manager.get_status(loop_id)
                if "error" in loop:
                    return {"success": False, "error": loop["error"]}
                return {
                    "success": True,
                    "loop": loop,
                    "iterations": iterations,
                }

            elif action == "list_all":
                status_filter = input.get("status")
                limit = input.get("limit", 50)
                loops = manager.list_loops(status=status_filter, limit=limit)
                return {"success": True, "loops": loops}

            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}. "
                             "Valid actions: pause, resume, cancel, get_details, get_history, list_all"
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
