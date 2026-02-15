from python.helpers.api import ApiHandler, Request, Response
from python.helpers.settings import PASSWORD_PLACEHOLDER, get_settings


class LangfuseTest(ApiHandler):

    async def process(self, input: dict, request: Request) -> dict | Response:
        public_key = input.get("public_key", "")
        secret_key = input.get("secret_key", "")
        host = input.get("host", "https://cloud.langfuse.com")

        # If frontend sent the masked placeholder, use the real stored key
        if secret_key == PASSWORD_PLACEHOLDER:
            secret_key = get_settings().get("langfuse_secret_key", "")

        if not public_key or not secret_key:
            return {"success": False, "error": "Public key and secret key are required"}

        try:
            from langfuse import Langfuse

            client = Langfuse(
                public_key=public_key,
                secret_key=secret_key,
                host=host,
            )
            result = client.auth_check()
            client.flush()
            return {"success": result, "error": "" if result else "Authentication failed"}
        except ImportError:
            return {"success": False, "error": "langfuse package not installed"}
        except Exception as e:
            return {"success": False, "error": str(e)}
