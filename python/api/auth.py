"""Authentication API endpoints."""
from datetime import datetime
from typing import Optional
from flask import Request, jsonify
from python.helpers.api import ApiHandler, Input, Output
from python.helpers.auth.user_manager import UserManager
from python.helpers.auth.session_manager import SessionManager, SessionContext
from python.helpers.auth.audit_log import AuditLogger
from python.helpers.auth.rbac import RBAC
from python.models.user import User
from python.models.role import Role
from python.models.permission import Permission
from python.models.team import Team
from python.database import get_db, init_db


class AuthRegister(ApiHandler):
    """Handle user registration."""

    @classmethod
    def requires_auth(cls) -> bool:
        return False

    @classmethod
    def requires_csrf(cls) -> bool:
        return False

    async def process(self, input: Input, request: Request) -> Output:
        """
        Register a new user.

        Expected input:
        {
            "username": "string",
            "email": "string",
            "password": "string",
            "full_name": "string" (optional)
        }
        """
        username = input.get("username")
        email = input.get("email")
        password = input.get("password")
        full_name = input.get("full_name")

        # Validation
        if not username or not email or not password:
            AuditLogger.log_from_request(
                action="auth.register_failed",
                request=request,
                status="failure",
                error_message="Missing required fields",
            )
            return jsonify({"error": "Username, email, and password are required"}), 400

        if len(password) < 8:
            return jsonify({"error": "Password must be at least 8 characters long"}), 400

        try:
            # Create user with default 'agent_user' role
            with get_db() as db:
                # Get default role
                default_role = db.query(Role).filter(Role.name == "agent_user").first()
                role_ids = [default_role.id] if default_role else []

                user = UserManager.create_user(
                    username=username,
                    email=email,
                    password=password,
                    full_name=full_name,
                    role_ids=role_ids,
                    db=db,
                )

                # Log successful registration
                AuditLogger.log_from_request(
                    action="user.create",
                    request=request,
                    user=None,
                    resource_type="user",
                    resource_id=str(user.id),
                    resource_name=user.username,
                    status="success",
                )

                return jsonify({
                    "message": "User registered successfully",
                    "user": user.to_dict(),
                }), 201

        except ValueError as e:
            AuditLogger.log_from_request(
                action="auth.register_failed",
                request=request,
                status="failure",
                error_message=str(e),
            )
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            AuditLogger.log_from_request(
                action="auth.register_failed",
                request=request,
                status="error",
                error_message=str(e),
            )
            return jsonify({"error": "Registration failed"}), 500


class AuthLogin(ApiHandler):
    """Handle user login."""

    @classmethod
    def requires_auth(cls) -> bool:
        return False

    @classmethod
    def requires_csrf(cls) -> bool:
        return False

    async def process(self, input: Input, request: Request) -> Output:
        """
        Authenticate user and return JWT tokens.

        Expected input:
        {
            "username": "string",  // or email
            "password": "string"
        }
        """
        username = input.get("username")
        password = input.get("password")

        if not username or not password:
            return jsonify({"error": "Username and password are required"}), 400

        try:
            # Authenticate user
            user = UserManager.authenticate(username, password)

            if not user:
                AuditLogger.log_from_request(
                    action="auth.login_failed",
                    request=request,
                    status="failure",
                    error_message="Invalid credentials",
                )
                return jsonify({"error": "Invalid credentials"}), 401

            # Create JWT tokens
            tokens = SessionManager.create_tokens(user)

            # Create session context
            SessionContext.create_session(user.id, {
                "user_id": user.id,
                "username": user.username,
                "team_id": user.team_id,
            })

            # Log successful login
            AuditLogger.log_from_request(
                action="auth.login",
                request=request,
                user=user,
                status="success",
            )

            return jsonify({
                "message": "Login successful",
                "user": user.to_dict(),
                **tokens,
            }), 200

        except Exception as e:
            AuditLogger.log_from_request(
                action="auth.login_failed",
                request=request,
                status="error",
                error_message=str(e),
            )
            return jsonify({"error": "Login failed"}), 500


class AuthLogout(ApiHandler):
    """Handle user logout."""

    async def process(self, input: Input, request: Request) -> Output:
        """Logout user and invalidate token."""
        user = SessionManager.get_user_from_request(request)

        if user:
            # End session context
            SessionContext.end_session(user.id)

            # Log logout
            AuditLogger.log_from_request(
                action="auth.logout",
                request=request,
                user=user,
                status="success",
            )

        return jsonify({"message": "Logout successful"}), 200


class AuthRefresh(ApiHandler):
    """Refresh access token using refresh token."""

    @classmethod
    def requires_auth(cls) -> bool:
        return False

    @classmethod
    def requires_csrf(cls) -> bool:
        return False

    async def process(self, input: Input, request: Request) -> Output:
        """
        Refresh access token.

        Expected input:
        {
            "refresh_token": "string"
        }
        """
        refresh_token = input.get("refresh_token")

        if not refresh_token:
            return jsonify({"error": "Refresh token is required"}), 400

        tokens = SessionManager.refresh_access_token(refresh_token)

        if not tokens:
            return jsonify({"error": "Invalid or expired refresh token"}), 401

        return jsonify(tokens), 200


class AuthMe(ApiHandler):
    """Get current user information."""

    async def process(self, input: Input, request: Request) -> Output:
        """Get current authenticated user details."""
        user = SessionManager.get_user_from_request(request)

        if not user:
            return jsonify({"error": "Not authenticated"}), 401

        return jsonify({"user": user.to_dict()}), 200


class AuthChangePassword(ApiHandler):
    """Change user password."""

    async def process(self, input: Input, request: Request) -> Output:
        """
        Change current user's password.

        Expected input:
        {
            "current_password": "string",
            "new_password": "string"
        }
        """
        user = SessionManager.get_user_from_request(request)

        if not user:
            return jsonify({"error": "Not authenticated"}), 401

        current_password = input.get("current_password")
        new_password = input.get("new_password")

        if not current_password or not new_password:
            return jsonify({"error": "Current password and new password are required"}), 400

        if len(new_password) < 8:
            return jsonify({"error": "Password must be at least 8 characters long"}), 400

        try:
            # Verify current password
            if not user.verify_password(current_password):
                AuditLogger.log_from_request(
                    action="auth.password_change",
                    request=request,
                    user=user,
                    status="failure",
                    error_message="Invalid current password",
                )
                return jsonify({"error": "Invalid current password"}), 400

            # Update password
            with get_db() as db:
                updated_user = UserManager.update_user(
                    user.id,
                    {"password": new_password},
                    db=db,
                )

                if not updated_user:
                    return jsonify({"error": "Failed to update password"}), 500

                # Log successful password change
                AuditLogger.log_from_request(
                    action="auth.password_change",
                    request=request,
                    user=user,
                    status="success",
                )

                return jsonify({"message": "Password changed successfully"}), 200

        except Exception as e:
            AuditLogger.log_from_request(
                action="auth.password_change",
                request=request,
                user=user,
                status="error",
                error_message=str(e),
            )
            return jsonify({"error": "Failed to change password"}), 500


class AuthInitialize(ApiHandler):
    """Initialize authentication system (permissions, roles, default admin)."""

    @classmethod
    def requires_auth(cls) -> bool:
        return False

    @classmethod
    def requires_csrf(cls) -> bool:
        return False

    async def process(self, input: Input, request: Request) -> Output:
        """
        Initialize the authentication system.

        Expected input (optional):
        {
            "admin_username": "string",
            "admin_email": "string",
            "admin_password": "string"
        }
        """
        try:
            # Initialize database tables
            init_db()

            # Initialize permissions
            RBAC.initialize_permissions()

            # Initialize roles
            RBAC.initialize_roles()

            # Create default admin user if it doesn't exist
            with get_db() as db:
                admin_user = db.query(User).filter(User.username == "admin").first()

                if not admin_user:
                    admin_username = input.get("admin_username", "admin")
                    admin_email = input.get("admin_email", "admin@agent-zero.local")
                    admin_password = input.get("admin_password", "admin123")

                    # Get admin role
                    admin_role = db.query(Role).filter(Role.name == "admin").first()

                    admin_user = UserManager.create_user(
                        username=admin_username,
                        email=admin_email,
                        password=admin_password,
                        full_name="System Administrator",
                        is_superuser=True,
                        is_active=True,
                        role_ids=[admin_role.id] if admin_role else [],
                        db=db,
                    )

                    AuditLogger.log_action(
                        action="user.create",
                        user_id=None,
                        resource_type="user",
                        resource_id=str(admin_user.id),
                        resource_name=admin_user.username,
                        status="success",
                        details={"note": "Initial admin user created during system initialization"},
                        db=db,
                    )

            return jsonify({
                "message": "Authentication system initialized successfully",
                "note": "Default admin user created (change password immediately)"
            }), 200

        except Exception as e:
            return jsonify({
                "error": "Failed to initialize authentication system",
                "details": str(e)
            }), 500


class AuthStatus(ApiHandler):
    """Get authentication system status."""

    @classmethod
    def requires_auth(cls) -> bool:
        return False

    @classmethod
    def requires_csrf(cls) -> bool:
        return False

    async def process(self, input: Input, request: Request) -> Output:
        """Get authentication system status and statistics."""
        try:
            with get_db() as db:
                user_count = db.query(User).count()
                role_count = db.query(Role).count()
                permission_count = db.query(Permission).count()
                team_count = db.query(Team).count()
                active_users = db.query(User).filter(User.is_active == True).count()

                active_sessions = SessionContext.get_active_session_count()

                # Get audit statistics
                audit_stats = AuditLogger.get_statistics(days=7, db=db)

                return jsonify({
                    "status": "operational",
                    "statistics": {
                        "users": {
                            "total": user_count,
                            "active": active_users,
                        },
                        "roles": role_count,
                        "permissions": permission_count,
                        "teams": team_count,
                        "active_sessions": active_sessions,
                    },
                    "audit": audit_stats,
                }), 200

        except Exception as e:
            return jsonify({
                "status": "error",
                "error": str(e)
            }), 500
