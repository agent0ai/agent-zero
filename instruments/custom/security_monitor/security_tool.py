import json
from python.helpers.security import SecurityManager
from python.helpers.notification import NotificationType, NotificationPriority, NotificationManager

def security_status_check():
    """Checks the current security authorization status for high-risk tools."""
    results = {}
    for tool in SecurityManager.HIGH_RISK_TOOLS:
        authorized = SecurityManager.is_tool_authorized(tool)
        results[tool] = "✅ AUTHORIZED" if authorized else "🔒 LOCKED (Requires Passkey)"
    
    return json.dumps({
        "status": "Ready",
        "enforcement_mode": "STRICT" if SecurityManager.ENFORCE_PASSKEY else "PASSIVE (Preview)",
        "tool_matrix": results
    }, indent=2)

def request_security_clearance(reason: str):
    """Explicitly requests a biometric signature from the user's mobile device."""
    NotificationManager.send_notification(
        type=NotificationType.AUTH_REQUIRED,
        priority=NotificationPriority.HIGH,
        message=f"Agent requested high-level clearance: {reason}",
        title="🛡️ Security Clearance Request",
        group="auth-gate"
    )
    return "SENT: Biometric request transmitted to registered mobile devices. Please check your phone."
