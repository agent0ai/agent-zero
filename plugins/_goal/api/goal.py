from __future__ import annotations

from agent import AgentContext
from helpers import team_access
from helpers.api import ApiHandler, Request, Response
from helpers.team_store import ADMIN_ACTOR_ID, get_store

from plugins._goal.tools import goal


class Goal(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        action = str(input.get("action", "") or "").strip().lower()
        context_id = str(input.get("context_id", "") or "").strip()
        member = team_access.request_scope()
        context = AgentContext.get(context_id) if context_id else None
        if member is not None or team_access.is_team_chat(context):
            with self.thread_lock:
                scope = team_access.request_chat_scope(context) if context else None
                if not scope or not scope.permits_chat(context) or not team_access.has_chat_history(context):
                    return Response("Chat access denied.", 403)
                run = get_store().active_run(context.id)
                if action != "get" and run and scope.account_id not in {run.account_id, ADMIN_ACTOR_ID}:
                    return Response("Only the run holder can change the active goal.", 409)
                return self._dispatch(action, context_id, {**input, "created_by": "user"})
        return self._dispatch(action, context_id, input)

    def _dispatch(self, action: str, context_id: str, input: dict) -> dict | Response:
        try:
            if action == "get":
                return {"ok": True, "goal": goal.public_goal(goal.get_goal(context_id))}
            if action in {"set", "create"}:
                return self._set(context_id, input)
            if action == "update":
                return self._update(context_id, input)
            if action == "pause":
                return self._status(context_id, "paused")
            if action == "resume":
                return self._status(context_id, "active")
            if action == "delete":
                goal.delete_goal(context_id)
                return {"ok": True, "goal": None}
        except FileNotFoundError:
            return Response(status=404, response="Goal not found")
        except ValueError as error:
            return Response(status=400, response=str(error))

        return Response(status=400, response=f"Unknown action: {action}")

    def _set(self, context_id: str, input: dict) -> dict:
        current_goal = goal.create_goal(
            context_id,
            str(input.get("objective") or ""),
            created_by=str(input.get("created_by") or "user"),
            token_budget=input.get("token_budget"),
        )
        return {"ok": True, "goal": goal.public_goal(current_goal)}

    def _update(self, context_id: str, input: dict) -> dict:
        current = goal.get_goal(context_id)
        updated_goal = goal.update_goal(
            context_id,
            objective=input.get("objective") if "objective" in input else None,
            status=input.get("status") if "status" in input else None,
            note=input.get("note") if "note" in input else None,
            token_budget=input.get("token_budget") if "token_budget" in input else None,
        )
        return {
            "ok": True,
            "goal": goal.public_goal(updated_goal),
            "reactivated": (
                current is not None
                and current.get("status") in goal.FINAL_STATUSES
                and updated_goal.get("status") == "active"
            ),
        }

    def _status(self, context_id: str, status: str) -> dict:
        current_goal = goal.update_goal(context_id, status=status)
        return {"ok": True, "goal": goal.public_goal(current_goal)}
