from python.helpers.api import ApiHandler, Request, Response
from python.helpers import files, notification, projects, notification
from python.helpers.plugins import import_plugin_module
memory = import_plugin_module("memory", "helpers/memory.py")
import os


class ReindexKnowledge(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        ctxid = input.get("ctxid", "")
        if not ctxid:
            raise Exception("No context id provided")
        context = self.use_context(ctxid)

        # reload memory to re-import knowledge
        await memory.Memory.reload(context.agent0)
        context.log.set_initial_progress()

        return {
            "ok": True,
            "message": "Knowledge re-indexed",
        }
