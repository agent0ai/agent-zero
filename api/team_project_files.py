import asyncio

from helpers import login, team_access, team_projects
from helpers.api import ApiHandler, Request, Response, session


class TeamProjectFiles(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        scope = team_access.request_scope()
        if not login.team_mode_enabled() or (scope is None and not login.is_admin_session(session)):
            return Response("Project files are forbidden.", 403)

        upload = None
        if request.mimetype == "multipart/form-data":
            input = request.form.to_dict()
            if input.get("action") != "upload" or not (upload := request.files.get("file")):
                return Response("Choose a project file to upload.", 400)
        if not isinstance(input, dict):
            return Response("Expected project file parameters.", 400)
        action, name = input.get("action"), input.get("project")
        if not isinstance(name, str) or (scope is not None and name not in scope.project_ids):
            return Response("Project access denied.", 403)
        if action not in ("limits", "list", "read", "info", "save", "mkdir", "download", "delete", "upload", "rename"):
            return Response("Unknown project file action.", 400)
        if action == "upload" and upload is None:
            return Response("Choose a project file to upload.", 400)

        def operate():
            with team_projects.project_lock(name, scope) as project_id:
                if action in ("limits", "list", "info"):
                    return team_projects.file_action(name, action, input)
                with team_projects.activity(f"project.file.{action}", scope.account_id if scope else "admin", project_id):
                    return team_projects.file_action(name, action, input, upload=upload)

        try:
            result = await asyncio.to_thread(operate)
        except team_projects.RevisionConflict as error:
            return Response(str(error), 409)
        except PermissionError:
            return Response("Project file access denied.", 403)
        except ValueError as error:
            return Response(str(error), 400)
        except OSError as error:
            message, status = team_projects.safe_file_error(error)
            return Response(message, status)
        return result if isinstance(result, Response) else {"ok": True, **result}
