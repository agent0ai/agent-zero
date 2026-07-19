from __future__ import annotations

from typing import Any

from plugins._goal.helpers import goals


def run(payload: dict[str, Any]) -> dict[str, Any]:
    invocation = payload.get("invocation") or {}
    raw_args = str(invocation.get("raw_arguments") or "").strip()
    tokens = ((invocation.get("arguments") or {}).get("tokens") or [])
    context_id = str((payload.get("context") or {}).get("context_id") or "").strip()

    if not context_id:
        return _effects(_toast("Open or create a chat context first.", level="error"))

    action = str(tokens[0] if tokens else "").strip().lower()

    try:
        if action in {"", "status", "show"}:
            return _show_markdown("Goal", goals.summarize_goal(goals.get_goal(context_id)))
        if action in {"pause", "paused"}:
            goal = goals.update_goal(context_id, status="paused")
            return _changed("Goal paused.", goal)
        if action in {"resume", "start", "active"}:
            goal = goals.update_goal(context_id, status="active")
            return _changed("Goal resumed.", goal)
        if action in {"delete", "clear", "remove"}:
            goals.delete_goal(context_id)
            return _changed("Goal deleted.", None)
        if action in {"complete", "done"}:
            goal = goals.update_goal(context_id, status="complete")
            return _changed("Goal marked complete.", goal)
        if action == "blocked":
            note = raw_args.split(None, 1)[1].strip() if len(tokens) > 1 else ""
            goal = goals.update_goal(context_id, status="blocked", note=note)
            return _changed("Goal marked blocked.", goal)
        if action == "edit":
            objective = raw_args.split(None, 1)[1].strip() if len(tokens) > 1 else ""
            goal = goals.update_goal(context_id, objective=objective, status="active")
            return _changed("Goal updated.", goal)
        if action in {"auto", "ask", "model"}:
            hint = raw_args.split(None, 1)[1].strip() if len(tokens) > 1 else ""
            return _auto_prompt(hint)

        goal = goals.create_goal(context_id, raw_args, created_by="user")
        return _changed("Goal set.", goal, send_text=raw_args)
    except FileNotFoundError:
        return _effects(_toast("No goal is set for this chat.", level="error"))
    except ValueError as error:
        return _effects(_toast(str(error), level="error"))


def _auto_prompt(hint: str) -> dict[str, Any]:
    prompt = (
        "Please create and manage a goal for this chat. Use the goal tools to inspect "
        "any current goal, create a concise goal objective, and update it when the work "
        "is complete or genuinely blocked."
    )
    if hint:
        prompt += f"\n\nUser hint: {hint}"
    return {"text": prompt, "effects": []}


def _changed(message: str, goal: dict[str, Any] | None, *, send_text: str = "") -> dict[str, Any]:
    return _effects(
        _toast(message),
        {"type": "goal_changed", "goal": goals.public_goal(goal)},
        {"type": "send_message", "text": send_text} if send_text else {},
    )


def _effects(*effects: dict[str, Any]) -> dict[str, Any]:
    return {"text": "", "effects": [effect for effect in effects if effect]}


def _toast(message: str, *, level: str = "success") -> dict[str, Any]:
    return {"type": "toast", "message": message, "level": level}


def _show_markdown(title: str, content: str) -> dict[str, Any]:
    return _effects({"type": "show_markdown", "title": title, "content": content})
