from python.helpers.extension import Extension
from python.helpers.secrets import get_secrets_manager


class MaskToolSecrets(Extension):

    async def execute(self, **kwargs):
        # model call data
        call_data:dict = kwargs.get("call_data", {})
            
        secrets_mgr = get_secrets_manager(self.agent.context)
        
        # mask system and user message
        if system:=call_data.get("system"):
            call_data["system"] = secrets_mgr.mask_values(system)
        if message:=call_data.get("message"):
            call_data["message"] = secrets_mgr.mask_values(message)