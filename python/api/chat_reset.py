from python.helpers import persist_chat
from python.helpers.api import ApiHandler, Input, Output, Request


class Reset(ApiHandler):
    async def process(self, input: Input, request: Request) -> Output:
        ctxid = input.get("context", "")

        # context instance - get or create
        context = self.use_context(ctxid)
        context.reset()
        persist_chat.save_tmp_chat(context)
        persist_chat.remove_msg_files(ctxid)

        return {
            "message": "Agent restarted.",
        }
