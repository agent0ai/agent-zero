from helpers.api import ApiHandler, Input, Output, Request, Response

from helpers import persist_chat, team_access

class ExportChat(ApiHandler):
    async def process(self, input: Input, request: Request) -> Output:
        ctxid = input.get("ctxid", "")
        if not ctxid:
            raise Exception("No context id provided")
        if team_access.is_team_chat_id(ctxid):
            return Response("Use the team audit to open a shared transcript.", 403)

        context = self.use_context(ctxid)
        content = persist_chat.export_json_chat(context)
        return {
            "message": "Chats exported.",
            "ctxid": context.id,
            "content": content,
        }
