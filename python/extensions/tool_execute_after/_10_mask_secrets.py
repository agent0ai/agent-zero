from python.helpers.extension import Extension
from python.helpers.secrets import SecretsManager
from python.helpers.tool import Response


class MaskToolSecrets(Extension):

    async def execute(self, response: Response | None = None, **kwargs):
        if not response:
            return
        secrets_mgr = SecretsManager.get_instance()
        response.message = secrets_mgr.mask_values(response.message)
