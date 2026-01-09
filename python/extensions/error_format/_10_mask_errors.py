from python.helpers.extension import Extension
from python.helpers.secrets import get_secrets_manager


class MaskErrorSecrets(Extension):

    async def execute(self, **kwargs):
        # Get error data from kwargs
        msg = kwargs.get("msg")
        if not msg:
            return

        secrets_mgr = get_secrets_manager(self.agent.context)

        # Mask the error message
        if "message" in msg:
            msg["message"] = secrets_mgr.mask_values(msg["message"])
