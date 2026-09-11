from helpers.extension import Extension
from plugins._a0_connector.helpers.ws_runtime import cancel_context_transfers


class CancelTransfers(Extension):
    def execute(self, data, **kwargs):
        context = data["args"][0]
        cancel_context_transfers(context.id)
