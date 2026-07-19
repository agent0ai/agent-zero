from __future__ import annotations

from helpers.api import ApiHandler, Request, Response

from plugins._goal.helpers import goals


class Goal(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        action = str(input.get("action", "") or "").strip().lower()
        context_id = str(input.get("context_id", "") or "").strip()

        try:
            if action == "get":
                return {"ok": True, "goal": goals.public_goal(goals.get_goal(context_id))}
            if action in {"set", "create"}:
                return self._set(context_id, input)
            if action == "update":
                return self._update(context_id, input)
            if action == "pause":
                return self._status(context_id, "paused")
            if action == "resume":
                return self._status(context_id, "active")
            if action == "delete":
                goals.delete_goal(context_id)
                return {"ok": True, "goal": None}
        except FileNotFoundError:
            return Response(status=404, response="Goal not found")
        except ValueError as error:
            return Response(status=400, response=str(error))

        return Response(status=400, response=f"Unknown action: {action}")

    def _set(self, context_id: str, input: dict) -> dict:
        goal = goals.create_goal(
            context_id,
            str(input.get("objective") or ""),
            created_by=str(input.get("created_by") or "user"),
            token_budget=input.get("token_budget"),
        )
        return {"ok": True, "goal": goals.public_goal(goal)}

    def _update(self, context_id: str, input: dict) -> dict:
        current = goals.get_goal(context_id)
        goal = goals.update_goal(
            context_id,
            objective=input.get("objective") if "objective" in input else None,
            status=input.get("status") if "status" in input else None,
            note=input.get("note") if "note" in input else None,
            token_budget=input.get("token_budget") if "token_budget" in input else None,
        )
        return {
            "ok": True,
            "goal": goals.public_goal(goal),
            "reactivated": (
                current is not None
                and current.get("status") in goals.FINAL_STATUSES
                and goal.get("status") == "active"
            ),
        }

    def _status(self, context_id: str, status: str) -> dict:
        goal = goals.update_goal(context_id, status=status)
        return {"ok": True, "goal": goals.public_goal(goal)}
