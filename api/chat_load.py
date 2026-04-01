from helpers.api import ApiHandler, Input, Output, Request, Response


from helpers import persist_chat

class LoadChats(ApiHandler):
    async def process(self, input: Input, request: Request) -> Output:
        chats = input.get("chats", [])
        if not chats:
            raise Exception("No chats provided")

        ctxids = persist_chat.load_json_chats(chats)

        from python.helpers.state_monitor_integration import mark_dirty_all
        mark_dirty_all(reason="api.chat_load.LoadChats")

        return {
            "message": "Chats loaded.",
            "ctxids": ctxids,
        }
