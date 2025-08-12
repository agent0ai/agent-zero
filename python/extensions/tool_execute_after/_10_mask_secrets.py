from python.helpers.extension import Extension
from python.helpers.secrets import SecretsManager


class MaskToolSecrets(Extension):

    async def execute(self, **kwargs):
        # Get response data from kwargs
        response_data = kwargs.get("response_data")
        if not response_data:
            return
            
        secrets_mgr = SecretsManager.get_instance()
        response = response_data["response"]
        
        # Mask response message if it exists
        if hasattr(response, "message") and response.message:
            response.message = secrets_mgr.mask_values(response.message)
        
        # Update the response data
        response_data["response"] = response
