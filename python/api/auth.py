"""
Authentication and Role-Based Access Control (RBAC) for Agent Zero.

Provides:
- User roles: admin, operator, viewer, agent
- Permission decorators for API endpoints
- Session-based authentication
- API key support for machine-to-machine
"""

import functools
import json
import threading
from typing import Dict, List, Set, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum

from flask import request, Response, session, redirect, url_for

from python.helpers import files, dotenv
from python.helpers.settings import get_settings


class Role(Enum):
    """User roles with increasing privileges."""
    VIEWER = "viewer"       # Read-only access
    OPERATOR = "operator"   # Can execute agents, view all data
    ADMIN = "admin"        # Full control, user management
    AGENT = "agent"        # Internal agent identity (machine)


@dataclass
class User:
    """User account with role and permissions."""
    username: str
    role: Role
    permissions: Set[str] = field(default_factory=set)
    api_key: Optional[str] = None
    is_active: bool = True

    def has_permission(self, permission: str) -> bool:
        """Check if user has a specific permission."""
        if permission in self.permissions:
            return True
        # Role-based implicit permissions
        if self.role == Role.ADMIN:
            return True  # Admin has all permissions
        if self.role == Role.OPERATOR and permission in ["agent:execute", "memory:read", "project:read"]:
            return True
        if self.role == Role.VIEWER and permission in ["memory:read", "project:read"]:
            return True
        return False


class RBACManager:
    """Manages users, roles, and permissions."""

    _instance: Optional['RBACManager'] = None
    _lock = threading.RLock()
    _users: Dict[str, User] = {}
    _api_keys: Dict[str, str] = {}  # api_key -> username mapping

    # Permission definitions
    PERMISSIONS = {
        # Agent operations
        "agent:execute": "Execute agents and tasks",
        "agent:create": "Create new agents",
        "agent:delete": "Delete agents",
        "agent:monitor": "Monitor agent execution",

        # Memory operations
        "memory:read": "Search and view memories",
        "memory:write": "Create and update memories",
        "memory:delete": "Delete memories",

        # Project operations
        "project:read": "View projects",
        "project:write": "Create/edit projects",
        "project:delete": "Delete projects",

        # Settings
        "settings:read": "View system settings",
        "settings:write": "Modify system settings",

        # User management (admin only)
        "user:read": "View users",
        "user:write": "Create/edit users",
        "user:delete": "Delete users",

        # System
        "system:logs": "View system logs",
        "system:metrics": "View Prometheus metrics",
        "system:backup": "Create/restore backups",
    }

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize default users from configuration."""
        self._load_users()

    def _load_users(self):
        """Load users from settings or default file."""
        # For now, create a default admin user from env vars
        admin_user = dotenv.get_dotenv_value("ADMIN_USER", "admin")
        admin_pass = dotenv.get_dotenv_value("ADMIN_PASSWORD")
        admin_api_key = dotenv.get_dotenv_value("ADMIN_API_KEY")

        if admin_user and admin_pass:
            # In production, this would come from a database
            self._users[admin_user] = User(
                username=admin_user,
                role=Role.ADMIN,
                permissions=list(self.PERMISSIONS.keys()),
                api_key=admin_api_key
            )
            if admin_api_key:
                self._api_keys[admin_api_key] = admin_user

        # Load additional users from file if exists
        users_file = files.get_abs_path("usr/users.json")
        if files.exists(users_file):
            content = files.read_file(users_file)
            try:
                users_data = json.loads(content)
                for user_data in users_data.get("users", []):
                    role = Role(user_data.get("role", "viewer"))
                    user = User(
                        username=user_data["username"],
                        role=role,
                        permissions=set(user_data.get("permissions", [])),
                        api_key=user_data.get("api_key")
                    )
                    self._users[user.username] = user
                    if user.api_key:
                        self._api_keys[user.api_key] = user.username
            except Exception as e:
                print(f"Warning: Failed to load users from {users_file}: {e}")

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        return self._users.get(username)

    def get_user_by_api_key(self, api_key: str) -> Optional[User]:
        """Get user by API key."""
        username = self._api_keys.get(api_key)
        if username:
            return self._users.get(username)
        return None

    def authenticate(self, username: str, password: str) -> Optional[User]:
        """Authenticate user with password."""
        # In production, use proper password hashing (bcrypt, argon2)
        stored_hash = dotenv.get_dotenv_value(f"USER_{username.upper()}_HASH")
        if stored_hash and stored_hash == password:  # TODO: implement proper hash check
            return self._users.get(username)
        return None

    def create_user(self, username: str, role: Role, password: Optional[str] = None, api_key: Optional[str] = None) -> User:
        """Create a new user."""
        with self._lock:
            if username in self._users:
                raise ValueError(f"User {username} already exists")

            # For simplicity, store password directly (NOT FOR PRODUCTION)
            if password:
                dotenv.save_dotenv_value(f"USER_{username.upper()}_HASH", password)

            user = User(username=username, role=role, api_key=api_key)
            self._users[username] = user
            if api_key:
                self._api_keys[api_key] = username
            return user

    def delete_user(self, username: str):
        """Delete a user."""
        with self._lock:
            if username in self._users:
                user = self._users[username]
                if user.api_key and user.api_key in self._api_keys:
                    del self._api_keys[user.api_key]
                del self._users[username]

    def list_users(self) -> List[Dict[str, Any]]:
        """List all users (without sensitive data)."""
        return [
            {
                "username": u.username,
                "role": u.role.value,
                "permissions": list(u.permissions),
                "has_api_key": u.api_key is not None,
                "is_active": u.is_active
            }
            for u in self._users.values()
        ]


# FastAPI/Flask decorators
def require_permission(permission: str):
    """Decorator to require a specific permission."""
    def decorator(f: Callable) -> Callable:
        @functools.wraps(f)
        async def decorated(*args, **kwargs):
            user = _get_current_user()
            if not user:
                return Response("Authentication required", 401)
            if not user.has_permission(permission):
                return Response(f"Permission denied: {permission}", 403)
            return await f(*args, **kwargs)
        return decorated
    return decorator


def require_role(role: Role):
    """Decorator to require a specific role."""
    def decorator(f: Callable) -> Callable:
        @functools.wraps(f)
        async def decorated(*args, **kwargs):
            user = _get_current_user()
            if not user:
                return Response("Authentication required", 401)
            # Role hierarchy: ADMIN > OPERATOR > VIEWER
            role_hierarchy = {Role.ADMIN: 4, Role.OPERATOR: 3, Role.VIEWER: 2, Role.AGENT: 1}
            if role_hierarchy.get(user.role, 0) < role_hierarchy.get(role, 0):
                return Response(f"Role {role.value} required", 403)
            return await f(*args, **kwargs)
        return decorated
    return decorator


def _get_current_user() -> Optional[User]:
    """Get the currently authenticated user from session or API key."""
    # Check session first (web UI)
    username = session.get("user")
    if username:
        rbac = RBACManager()
        return rbac.get_user_by_username(username)

    # Check API key
    api_key = request.headers.get("X-API-KEY")
    if api_key:
        rbac = RBACManager()
        return rbac.get_user_by_api_key(api_key)

    return None


# API handlers for user management (admin only)
from python.api import ApiHandler

class UsersHandler(ApiHandler):
    """API handler for user management."""

    requires_auth = True
    requires_api_key = False

    @classmethod
    def get_methods(cls):
        return ["GET", "POST", "DELETE"]

    async def handle_request(self, request):
        rbac = RBACManager()

        if request.method == "GET":
            # List users
            users = rbac.list_users()
            return Response(json.dumps({"users": users}), mimetype="application/json")

        elif request.method == "POST":
            # Create user (admin only)
            current_user = _get_current_user()
            if not current_user or current_user.role != Role.ADMIN:
                return Response("Admin role required", 403)

            data = request.get_json()
            username = data.get("username")
            role_str = data.get("role", "viewer")
            password = data.get("password")
            api_key = data.get("api_key")

            try:
                role = Role(role_str)
            except ValueError:
                return Response(f"Invalid role: {role_str}", 400)

            user = rbac.create_user(username=username, role=role, password=password, api_key=api_key)
            return Response(json.dumps({"status": "created", "user": user.username}), mimetype="application/json")

        elif request.method == "DELETE":
            # Delete user (admin only)
            current_user = _get_current_user()
            if not current_user or current_user.role != Role.ADMIN:
                return Response("Admin role required", 403)

            username = request.args.get("username")
            if not username:
                return Response("Username required", 400)

            rbac.delete_user(username)
            return Response(json.dumps({"status": "deleted", "user": username}), mimetype="application/json")
