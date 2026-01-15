from python.helpers.api import ApiHandler, Request, Response
from python.helpers.security import SecurityManager

class SecurityOps(ApiHandler):
    """API handler for specialized security operations (Audit, Panic Lock)."""

    async def process(self, input: dict, request: Request) -> dict | Response:
        action = input.get("action")
        user_id = input.get("user_id", "default_user")

        try:
            if action == "get_audit_logs":
                # Ensure user is authorized to see logs (optional Passkey check here?)
                logs = SecurityManager.get_audit_logs(limit=input.get("limit", 50))
                return {"success": True, "logs": logs}
                
            elif action == "panic_lock":
                SecurityManager.panic_lock(user_id)
                return {"success": True, "message": "All sessions revoked. Re-authorization required."}
                
            elif action == "toggle_enforcement":
                # Only allow if we have some admin flag or specific session
                enabled = input.get("enabled", False)
                SecurityManager.ENFORCE_PASSKEY = enabled
                return {"success": True, "enforced": SecurityManager.ENFORCE_PASSKEY}

            return {"success": False, "error": f"Unknown security action: {action}"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
