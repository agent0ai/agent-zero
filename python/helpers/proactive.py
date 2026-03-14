import json
import os

from python.helpers import files

try:
    from instruments.custom.workflow_engine.workflow_db import WorkflowEngineDatabase
except Exception:
    WorkflowEngineDatabase = None

# Optional: pywebpush for push notifications
try:
    from pywebpush import WebPushException, webpush

    PYWEBPUSH_AVAILABLE = True
except ImportError:
    webpush = None
    WebPushException = Exception
    PYWEBPUSH_AVAILABLE = False


class ProactiveManager:
    """Manages proactive alerts and push notifications for the user."""

    # Toggle for feature rollout
    ENABLED = False
    LOG_OPTIONAL_WARNINGS = os.getenv("A0_LOG_OPTIONAL_WARNINGS", "").strip().lower() in {"1", "true", "yes", "on"}

    # VAPID Claims
    VAPID_CLAIMS = {"sub": "mailto:admin@agent-jumbo.local"}

    @classmethod
    def get_public_key(cls):
        """Retrieves the public key for frontend subscription."""
        from python.helpers.security import SecurityVaultManager

        SecurityVaultManager.initialize_keys()
        return SecurityVaultManager.get_secret(
            "VAPID_PUBLIC_KEY",
            "BEl62iC769AsE_YQ-bMIn2404u2S5yTzOsVIdgYxOnvIowh-G5hV_Iq12_9E2D8y",  # pragma: allowlist secret
        )

    @classmethod
    def get_private_key(cls):
        """Retrieves the private key for signing push payloads."""
        from python.helpers.security import SecurityVaultManager

        SecurityVaultManager.initialize_keys()
        return SecurityVaultManager.get_secret("VAPID_PRIVATE_KEY", "PLACEHOLDER_PRIVATE_KEY")

    @classmethod
    def send_push(cls, user_id, title, body, url="/", actions=None, requestId=None):
        """Sends a physical push notification to a registered user device."""
        if not cls.ENABLED:
            return False
        if webpush is None:
            return False

        try:
            if WorkflowEngineDatabase is None:
                return False
            db_path = files.get_abs_path("./instruments/custom/workflow_engine/data/workflow.db")
            db = WorkflowEngineDatabase(db_path)
            conn = db._get_conn()
            cursor = conn.cursor()
            cursor.execute("SELECT push_subscription FROM user_profiles WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            conn.close()

            if not row or not row[0]:
                print(f"No push subscription for user {user_id}")
                return False

            subscription_info = json.loads(row[0])

            payload = {"title": title, "body": body, "url": url}
            if actions:
                payload["actions"] = actions
            if requestId:
                payload["requestId"] = requestId

            webpush(
                subscription_info=subscription_info,
                data=json.dumps(payload),
                vapid_private_key=cls.get_private_key(),
                vapid_claims=cls.VAPID_CLAIMS,
            )
            return True
        except WebPushException as ex:
            print(f"Push failed: {ex}")
            return False
        except Exception as e:
            print(f"Proactive Error: {e}")
            return False

    @classmethod
    def check_and_nudge(cls, user_id="default_user"):
        """Analyzes synced context and sends nudges if necessary."""
        try:
            from instruments.custom.workflow_engine.workflow_db import WorkflowEngineDatabase
            from python.api.profile_sync import ProfileSync

            db_path = files.get_abs_path("./instruments/custom/workflow_engine/data/workflow.db")
            db = WorkflowEngineDatabase(db_path)

            resp = ProfileSync()._get_profile(db, user_id)
            if not resp.get("success") or not resp.get("profile"):
                return

            profile = resp["profile"]
            device_info = profile.get("device_info", {})
            battery = device_info.get("battery")

            # Example: Low Battery Nudge
            if battery and battery.get("level", 100) < 20 and not battery.get("charging"):
                cls.send_push(
                    user_id,
                    "🔋 Low Battery Alert",
                    f"Your phone is at {battery['level']}%. Need me to wrap up anything before it dies?",
                    "/",
                )

            # Example: Security nudge - check if MFA is enabled
            if not profile.get("mfa_enabled"):
                # We could nudge once a week, etc.
                pass

        except Exception as e:
            if cls.LOG_OPTIONAL_WARNINGS:
                print(f"Nudge Check Error: {e}")

    @classmethod
    def notify_tool_usage(cls, tool_name, user_id="default_user"):
        """Nudge user when a sensitive tool is being accessed."""
        sensitive_tools = ["run_in_terminal", "run_command", "write_file", "delete_file", "email"]
        if any(st in tool_name.lower() for st in sensitive_tools):
            cls.send_push(
                user_id, title="🛡️ Security Monitor", body=f"Agent is accessing sensitive tool: {tool_name}", url="/logs"
            )
            return True
        return False
