
from python.helpers.api import ApiHandler, Request, Response
from python.helpers.security import SecurityManager


class PasskeyAuth(ApiHandler):
    """API handler for Passkey (WebAuthn) registration and authentication."""

    async def process(self, input: dict, request: Request) -> dict | Response:
        action = input.get("action")
        user_id = input.get("user_id", "admin")
        username = input.get("username", "AgentZeroUser")

        # Security: Rate Limiting
        if not SecurityManager.check_rate_limit(f"passkey_{action}", limit=10, window=300):
            return {"success": False, "error": "Rate limit exceeded. Try again in a few minutes."}

        try:
            from instruments.custom.workflow_engine.workflow_db import WorkflowEngineDatabase
            from python.helpers.passkey_vault import PasskeyVaultManager

            # Initialize the passkey manager with database
            db = WorkflowEngineDatabase()
            manager = PasskeyVaultManager(db)

            # Get host and origin from request headers for WebAuthn
            host = request.headers.get("Host", "localhost").split(":")[0]
            origin = request.headers.get("Origin", f"http://{host}")

            if action == "get_registration_options":
                options = manager.get_registration_options(user_id, username, host)
                SecurityManager.log_event("passkey_reg_init", "success", user_id)
                return {"success": True, "options": options}

            elif action == "verify_registration":
                challenge = input.get("challenge")
                response_data = input.get("response")
                result = manager.verify_registration(user_id, challenge, response_data, host, origin)

                status = "success" if result.get("success") else "failure"
                SecurityManager.log_event("passkey_reg_verify", status, user_id, details=result if status == "failure" else None)
                return result

            elif action == "get_authentication_options":
                options = manager.get_authentication_options(user_id, host)
                SecurityManager.log_event("passkey_auth_init", "success", user_id)
                return {"success": True, "options": options}

            elif action == "verify_authentication":
                challenge = input.get("challenge")
                response_data = input.get("response")
                result = manager.verify_authentication(user_id, challenge, response_data, host, origin)

                status = "success" if result.get("success") else "failure"
                if status == "success":
                    SecurityManager.set_authorized(user_id)

                SecurityManager.log_event("passkey_auth_verify", status, user_id, details=result if status == "failure" else None)
                return result

            return {"success": False, "error": f"Unknown action: {action}"}

        except Exception as e:
            return {"success": False, "error": str(e)}
