from python.helpers.api import ApiHandler, Request, Response
from python.helpers import files, notification, projects, notification, runtime, settings
from python.helpers.plugins import import_plugin_module
memory = import_plugin_module("memory", "helpers/memory.py")
import os


class GetChatFilesPath(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        ctxid = input.get("ctxid", "")
        if not ctxid:
            raise Exception("No context id provided")
        context = self.use_context(ctxid)

        project_name = projects.get_context_project_name(context)
        if project_name:
            folder = files.normalize_a0_path(projects.get_project_folder(project_name))
        else:
            folder = settings.get_settings()["workdir_path"]

        return {
            "ok": True,
            "path": folder,
        }