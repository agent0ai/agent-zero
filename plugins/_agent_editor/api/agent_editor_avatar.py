from __future__ import annotations

from flask import send_file

from helpers.api import ApiHandler, Request, Response
from plugins._agent_editor.helpers import editor


class AgentEditorAvatar(ApiHandler):
    @classmethod
    def get_methods(cls) -> list[str]:
        return ["GET", "POST"]

    async def process(self, input: dict, request: Request) -> dict | Response:
        try:
            if request.method == "POST":
                return {
                    "ok": True,
                    **editor.stage_avatar(request.files.get("avatar")),
                }

            profile_id = editor.validate_profile_id(request.args.get("profile_id"))
            project_name = str(request.args.get("project_name") or "").strip()
            if project_name:
                project_name = editor.projects.validate_project_name(project_name)
            path = editor.effective_avatar_path(
                profile_id,
                editor._EditorContext(project_name),
            )
            if not path or not path.is_file():
                return Response(status=404, response="Avatar not found.")
            response = send_file(path, mimetype="image/webp", conditional=True)
            response.headers["Cache-Control"] = "private, no-cache"
            return response
        except ValueError as exc:
            return Response(status=400, response=str(exc), mimetype="text/plain")
