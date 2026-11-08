from helpers.api import ApiHandler, Request, Response
from helpers import files, projects, settings


class GetChatFilesPath(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        ctxid = input.get("ctxid", "")
        if not ctxid:
            raise Exception("No context id provided")
        context = self.use_context(ctxid)

        project_name = projects.get_context_project_name(context)
        if project_name:
            folder = projects.get_project_folder(project_name)
        else:
            folder = settings.get_settings()["workdir_path"]

        return {
            "ok": True,
            "path": files.fix_dev_path(folder) if folder else folder,
        }
