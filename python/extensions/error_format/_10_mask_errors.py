from python.helpers.extension import Extension
from python.helpers.secrets import SecretsManager


class MaskErrorSecrets(Extension):

    async def execute(self, **kwargs):
        # Get error data from kwargs
        msg = kwargs.get("msg")
        if not msg:
            return

        secrets_mgr = SecretsManager.get_instance()

        # Mask the error message
        if "message" in msg:
            msg["message"] = secrets_mgr.mask_values(msg["message"])
