import time
import json
import os
from flask import request
from python.helpers import files

class SecurityManager:
    """Manages white-hat security protections, auditing, and rate limiting."""
    
    _rate_limits = {} # simple in-memory rate limiting. {ip_action: [timestamps]}
    _authorized_sessions = {} # {user_id: last_authorized_time}
    
    # Toggle for feature rollout
    ENFORCE_PASSKEY = False 
    
    HIGH_RISK_TOOLS = [
        "code_execution_tool", "email", "email_advanced", 
        "memory_delete", "memory_forget", "workflow_engine", 
        "run_in_terminal", "cowork_approval", "memory_access"
    ]

    @classmethod
    def is_tool_authorized(cls, tool_name, user_id="default_user"):
        """Checks if a tool requires authorization and if the user is currently verified."""
        if not cls.ENFORCE_PASSKEY:
            return True
            
        if tool_name not in cls.HIGH_RISK_TOOLS:
            return True
        
        last_auth = cls._authorized_sessions.get(user_id, 0)
        # Authorization valid for 1 hour
        if time.time() - last_auth < 3600:
            return True
        
        return False

    @classmethod
    def set_authorized(cls, user_id="default_user"):
        """Marks the user as authorized for high-risk operations."""
        cls._authorized_sessions[user_id] = time.time()
        cls.log_event("session_authorized", "success", user_id)

    @staticmethod
    def log_event(event_type, status, user_id="default_user", details=None):
        """Logs a security event to the audit table."""
        try:
            from instruments.custom.workflow_engine.workflow_db import WorkflowEngineDatabase
            db_path = files.get_abs_path("./instruments/custom/workflow_engine/data/workflow.db")
            db = WorkflowEngineDatabase(db_path)
            conn = db._get_conn()
            cursor = conn.cursor()
            
            ip = request.remote_addr if request else "unknown"
            ua = request.headers.get("User-Agent") if request else "unknown"
            
            cursor.execute("""
                INSERT INTO security_audit_log (event_type, status, user_id, ip_address, device_info, details)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (event_type, status, user_id, ip, ua, json.dumps(details) if details else None))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"FAILED TO LOG SECURITY EVENT: {e}")

    @classmethod
    def check_rate_limit(cls, action, limit=5, window=60):
        """
        Simple rate limiter. 
        action: string identifier for the action
        limit: max attempts
        window: seconds
        """
        ip = request.remote_addr
        key = f"{ip}_{action}"
        now = time.time()
        
        if key not in cls._rate_limits:
            cls._rate_limits[key] = []
            
        # Clean old timestamps
        cls._rate_limits[key] = [t for t in cls._rate_limits[key] if now - t < window]
        
        if len(cls._rate_limits[key]) >= limit:
            cls.log_event("rate_limit_exceeded", "warning", details={"action": action, "limit": limit})
            return False
            
        cls._rate_limits[key].append(now)
        return True

    @staticmethod
    def validate_input(data, required_fields):
        """Basic input validation and sanitization."""
        if not data or not isinstance(data, dict):
            return False, "Invalid input format"
            
        for field in required_fields:
            if field not in data:
                return False, f"Missing required field: {field}"
                
        return True, None

class SecurityVaultManager:
    """Manages sensitive keys and secrets that are hardware-bound or encrypted."""
    
    VAULT_PATH = "./data/secure_vault.json"

    @classmethod
    def initialize_keys(cls):
        """Ensures fundamental security keys (like VAPID) exist."""
        if not cls.get_secret("VAPID_PRIVATE_KEY"):
            try:
                # Generate VAPID keys if pywebpush is available
                from pywebpush import webpush
                import ecdsa
                import base64
                
                # Generate a NIST P-256 key pair
                sk = ecdsa.SigningKey.generate(curve=ecdsa.NIST256p)
                vk = sk.get_verifying_key()
                
                private_key = base64.urlsafe_b64encode(sk.to_string()).decode('utf-8').strip("=")
                public_key = base64.urlsafe_b64encode(b"\x04" + vk.to_string()).decode('utf-8').strip("=")
                
                cls.set_secret("VAPID_PRIVATE_KEY", private_key)
                cls.set_secret("VAPID_PUBLIC_KEY", public_key)
                print("[🔐 Security] Generated new VAPID keypair for proactive alerts.")
            except Exception as e:
                print(f"[⚠️ Security] Failed to generate VAPID keys: {e}")

    @classmethod
    def get_secret(cls, key_name, default=None):
        """Retrieves a secret from the secure vault (ideally encrypted in production)."""
        abs_path = files.get_abs_path(cls.VAULT_PATH)
        if not os.path.exists(abs_path):
            return default
            
        try:
            with open(abs_path, 'r') as f:
                vault = json.load(f)
            return vault.get(key_name, default)
        except:
            return default

    @classmethod
    def set_secret(cls, key_name, value):
        """Sets a secret in the vault."""
        abs_path = files.get_abs_path(cls.VAULT_PATH)
        files.ensure_dir(os.path.dirname(abs_path))
        
        vault = {}
        if os.path.exists(abs_path):
            try:
                with open(abs_path, 'r') as f:
                    vault = json.load(f)
            except:
                pass
        
        vault[key_name] = value
        with open(abs_path, 'w') as f:
            json.dump(vault, f)
        return True
