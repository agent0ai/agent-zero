from helpers.extension import Extension


RESPONSE_KEY = "_context_window_accepted_response"


class DrainProviderUsage(Extension):
    def execute(self, data: dict, **kwargs):
        callback = data["kwargs"].get("response_callback")
        if callback is None:
            return

        async def drain_callback(chunk: str, full: str):
            response = await callback(chunk, full)
            if response is not None and RESPONSE_KEY not in data:
                data[RESPONSE_KEY] = response
            return None

        data["kwargs"]["response_callback"] = drain_callback
