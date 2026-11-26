from helpers import projects, team_projects, team_runs
from helpers.tool import Response


_REVISIONS = "_team_text_editor_revisions"


def execute(agent, action: str, args: dict) -> Response:
    try:
        run, scope = team_runs.executing_scope(agent.context)
        name = projects.get_context_project_name(agent.context)
        path = args.get("path")
        team_projects.file_parts(path)
        revisions = agent.get_data(_REVISIONS) or {}
        with team_projects.project_lock(name, scope) as project_id:
            with team_projects.activity(f"tool.text_editor.{action}", run.account_id, project_id, context_id=run.context_id):
                result = _operate(name, path, action, args, revisions, agent)
        return Response(message=result, break_loop=False)
    except (PermissionError, ValueError) as error:
        return Response(message=str(error), break_loop=False)
    except OSError as error:
        return Response(message=team_projects.safe_file_error(error)[0], break_loop=False)


def _operate(name, path, action, args, revisions, agent):
    if action == "read":
        start = args.get("line_from", 1)
        end = args.get("line_to")
        if type(start) is not int or start < 1 or (end is not None and (type(end) is not int or end < start)):
            raise ValueError("Choose a valid one-based line range.")
        loaded = team_projects.file_action(name, "read", {"path": path})
        lines = loaded["content"].splitlines()
        end = min(len(lines), start + 199, end if end is not None else start + 149)
        text = "\n".join(f"{number} | {lines[number - 1]}" for number in range(start, end + 1))
        revisions[path] = loaded["revision"]
        agent.set_data(_REVISIONS, revisions)
        visible = text[:20_000]
        suffix = "\n[Output cropped]" if len(visible) < len(text) else ""
        return f"{path} ({len(lines)} lines)\n{visible}{suffix}"

    if action not in ("write", "patch"):
        raise ValueError("Choose the read, write or patch action.")
    revision = revisions.get(path)
    content = args.get("content")
    if action == "patch":
        if not revision:
            raise ValueError("Read this file before patching it.")
        current = team_projects.file_action(name, "read", {"path": path})
        team_projects.require_revision(revision, current["revision"])
        old, new = args.get("old_text"), args.get("new_text")
        if not isinstance(old, str) or not old or not isinstance(new, str):
            raise ValueError("Provide old_text and new_text for one exact replacement.")
        if current["content"].count(old) != 1:
            raise ValueError("old_text must match exactly one span in the file.")
        content = current["content"].replace(old, new, 1)
    result = team_projects.file_action(name, "save", {"path": path, "content": content, "revision": revision})
    revisions[path] = result["revision"]
    agent.set_data(_REVISIONS, revisions)
    return f"Saved {path} ({result['size']} bytes)."
