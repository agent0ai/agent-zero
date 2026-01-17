from python.helpers.api import ApiHandler, Request


class PromptEnhanceGet(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict:
        ctxid = input.get("context", "")
        try:
            context = self.use_context(ctxid, create_if_not_exists=False)
        except Exception:
            return {"data": None}

        data = context.get_output_data("prompt_enhance_last")
        return {"data": data}
