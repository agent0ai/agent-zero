from python.helpers.extension import Extension
from python.helpers.secrets import SecretsManager


class MaskToolSecrets(Extension):

    async def execute(self, **kwargs):
        # model call data
        call_data:dict = kwargs.get("call_data", {})
            
        secrets_mgr = SecretsManager.get_instance()
        
        # mask system and user message
        if system:=call_data.get("system"):
            call_data["system"] = secrets_mgr.mask_values(system)
        if message:=call_data.get("message"):
            call_data["message"] = secrets_mgr.mask_values(message)