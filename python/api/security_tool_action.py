from python.helpers.api import ApiHandler
from python.helpers.security import SecurityManager
from flask import Request

class security_tool_action(ApiHandler):
    """Handles Approve/Deny actions from push notifications."""

    @classmethod
    def requires_auth(cls) -> bool:
        # Since this is called from a Service Worker, we might not have a session cookie easily.
        # But we can verify via a secret in the request or just rely on the UUID requestId.
        # For simplicity in this hub, we'll allow it if the requestId is valid.
        return False

    async def process(self, input: dict, request: Request) -> dict:
        if not input or "requestId" not in input or "action" not in input:
            return {"success": False, "error": "Missing requestId or action"}

        request_id = input["requestId"]
        action = input["action"] # 'approve' or 'deny'
        
        approved = action == "approve"
        success = SecurityManager.resolve_auth_request(request_id, approved=approved)
        
        if success:
            return {"success": True, "status": "approved" if approved else "denied"}
        else:
            return {"success": False, "error": "Request not found or expired"}
