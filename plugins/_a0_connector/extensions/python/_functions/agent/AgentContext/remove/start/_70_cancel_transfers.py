from helpers.extension import Extension
from plugins._a0_connector.helpers.ws_runtime import cancel_context_transfers


class CancelTransfers(Extension):
    def execute(self, data, **kwargs):
        context_id = data["args"][0] if data["args"] else data["kwargs"]["id"]
        cancel_context_transfers(context_id)
