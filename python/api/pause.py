from python.helpers.api import ApiHandler, Request, Response


class Pause(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        # input data
        paused = input.get("paused", False)
        ctxid = input.get("context", "")

        # context instance - get or create
        context = self.use_context(ctxid)

        context.paused = paused
        if not paused:
            context.resume_queued()

        dispatch = context.get_dispatch_status()
        return {
            "message": "Agent paused." if paused else "Agent unpaused.",
            "pause": paused,
            "runtime_state": context.get_output_data("runtime_state"),
            "queue_depth": context.get_output_data("chat_queue_depth"),
            "dispatch": dispatch,
        }
