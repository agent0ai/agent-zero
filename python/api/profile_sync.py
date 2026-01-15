from python.helpers.api import ApiHandler, Request, Response
from python.helpers import files
from python.helpers.security import SecurityManager
import os
import json
from datetime import datetime

class ProfileSync(ApiHandler):
    """API handler for syncing phone profile data (Android/Apple)."""

    async def process(self, input: dict, request: Request) -> dict | Response:
        action = input.get("action")
        user_id = input.get("user_id", "default_user")
        
        # Security: Rate Limiting
        if not SecurityManager.check_rate_limit("profile_sync", limit=20, window=300):
            return {"success": False, "error": "Rate limit exceeded."}

        try:
            from instruments.custom.workflow_engine.workflow_db import WorkflowEngineDatabase
            db = WorkflowEngineDatabase()

            if action == "update_profile":
                valid, err = SecurityManager.validate_input(input, ["profile"])
                if not valid: return {"success": False, "error": err}
                
                profile_data = input.get("profile", {})
                result = self._update_profile(db, user_id, profile_data)
                SecurityManager.log_event("profile_sync", "success", user_id)
                return result
                
            elif action == "get_profile":
                return self._get_profile(db, user_id)

            elif action == "update_push_subscription":
                subscription = input.get("subscription")
                return self._update_push_subscription(db, user_id, subscription)

            elif action == "get_push_key":
                from python.helpers.proactive import ProactiveManager
                return {"success": True, "publicKey": ProactiveManager.get_public_key()}
                
            return {"success": False, "error": f"Unknown action: {action}"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _update_push_subscription(self, db, user_id, subscription):
        conn = db._get_conn()
        cursor = conn.cursor()
        
        cursor.execute("UPDATE user_profiles SET push_subscription = ? WHERE user_id = ?", 
                       (json.dumps(subscription), user_id))
        
        conn.commit()
        conn.close()
        return {"success": True}

    def _update_profile(self, db, user_id, data):
        conn = db._get_conn()
        cursor = conn.cursor()
        
        # Check if exists
        cursor.execute("SELECT user_id FROM user_profiles WHERE user_id = ?", (user_id,))
        exists = cursor.fetchone()
        
        now = datetime.now().isoformat()
        
        if exists:
            cursor.execute("""
                UPDATE user_profiles SET 
                    full_name = ?, email = ?, phone_number = ?, 
                    avatar_url = ?, device_info = ?, timezone = ?, 
                    locale = ?, last_synced = ?
                WHERE user_id = ?
            """, (
                data.get("fullName"), data.get("email"), data.get("phone"),
                data.get("avatarUrl"), json.dumps(data.get("deviceInfo", {})),
                data.get("timezone"), data.get("locale"), now, user_id
            ))
        else:
            cursor.execute("""
                INSERT INTO user_profiles 
                (user_id, full_name, email, phone_number, avatar_url, device_info, timezone, locale, last_synced)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id, data.get("fullName"), data.get("email"), data.get("phone"),
                data.get("avatarUrl"), json.dumps(data.get("deviceInfo", {})),
                data.get("timezone"), data.get("locale"), now
            ))
            
        conn.commit()
        conn.close()
        return {"success": True, "last_synced": now}

    def _get_profile(self, db, user_id):
        conn = db._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user_profiles WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            profile = dict(row)
            if profile.get("device_info"):
                profile["device_info"] = json.loads(profile["device_info"])
            return {"success": True, "profile": profile}
        return {"success": True, "profile": None}
