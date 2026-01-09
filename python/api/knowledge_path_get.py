from python.helpers.api import ApiHandler, Request, Response
from python.helpers import files, memory, notification, projects, notification
import os
from werkzeug.utils import secure_filename


class GetKnowledgePath(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        ctxid = input.get("ctxid", "")
        if not ctxid:
            raise Exception("No context id provided")
        context = self.use_context(ctxid)

        project_name = projects.get_context_project_name(context)
        if project_name:
            knowledge_folder = projects.get_project_meta_folder(project_name, "knowledge")
        else:
            knowledge_folder = memory.get_custom_knowledge_subdir_abs(context.agent0)

        knowledge_folder = files.normalize_a0_path(knowledge_folder)

        return {
            "ok": True,
            "path": knowledge_folder,
        }