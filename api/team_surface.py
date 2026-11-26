import asyncio

from helpers import team_access, team_projects, team_surfaces
from helpers.api import ApiHandler, Request, Response


class TeamSurface(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        if not isinstance(input, dict):
            return Response("Invalid project viewer request.", 400)
        scope = team_access.request_scope()
        project = input.get("project")
        mode = input.get("mode")
        action = input.get("action", "open")
        path = input.get("path", "")
        if scope is None or not isinstance(project, str) or project not in scope.project_ids:
            return Response("Project access denied.", 403)
        if not all(isinstance(value, str) for value in (mode, action, path)):
            return Response("Invalid project viewer request.", 400)
        try:
            return await asyncio.to_thread(team_surfaces.operation, scope, project, mode, action, path)
        except team_projects.RevisionConflict as error:
            return Response(str(error), 409)
        except PermissionError:
            return Response("Project access denied.", 403)
        except ValueError as error:
            return Response(str(error), 400)
        except RuntimeError as error:
            return Response(str(error), 503)
        except OSError as error:
            message, status = team_projects.safe_file_error(error)
            return Response(message, status)
