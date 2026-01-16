"""User management API endpoints."""
from flask import Request, jsonify
from python.helpers.api import ApiHandler, Input, Output
from python.helpers.auth.user_manager import UserManager
from python.helpers.auth.session_manager import SessionManager
from python.helpers.auth.audit_log import AuditLogger, audit_log
from python.helpers.auth.rbac import require_permission, RBAC
from python.models.user import User
from python.database import get_db


class UsersList(ApiHandler):
    """List all users."""

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["GET", "POST"]

    async def process(self, input: Input, request: Request) -> Output:
        """
        List users with pagination and filtering.

        Query parameters:
        - skip: int (default: 0)
        - limit: int (default: 100)
        - team_id: int (optional)
        - is_active: bool (optional)
        - search: string (optional)
        """
        current_user = SessionManager.get_user_from_request(request)

        if not current_user:
            return jsonify({"error": "Authentication required"}), 401

        if not RBAC.check_permission(current_user, "user.read"):
            return jsonify({"error": "Permission denied"}), 403

        skip = int(input.get("skip", 0))
        limit = int(input.get("limit", 100))
        team_id = input.get("team_id")
        is_active = input.get("is_active")
        search = input.get("search")

        try:
            with get_db() as db:
                users = UserManager.list_users(
                    skip=skip,
                    limit=limit,
                    team_id=int(team_id) if team_id else None,
                    is_active=bool(is_active) if is_active is not None else None,
                    search=search,
                    db=db,
                )

                return jsonify({
                    "users": [user.to_dict() for user in users],
                    "count": len(users),
                    "skip": skip,
                    "limit": limit,
                }), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500


class UsersCreate(ApiHandler):
    """Create a new user."""

    async def process(self, input: Input, request: Request) -> Output:
        """
        Create a new user.

        Expected input:
        {
            "username": "string",
            "email": "string",
            "password": "string",
            "full_name": "string" (optional),
            "team_id": int (optional),
            "role_ids": [int] (optional),
            "is_active": bool (default: true)
        }
        """
        current_user = SessionManager.get_user_from_request(request)

        if not current_user:
            return jsonify({"error": "Authentication required"}), 401

        if not RBAC.check_permission(current_user, "user.create"):
            return jsonify({"error": "Permission denied"}), 403

        username = input.get("username")
        email = input.get("email")
        password = input.get("password")
        full_name = input.get("full_name")
        team_id = input.get("team_id")
        role_ids = input.get("role_ids")
        is_active = input.get("is_active", True)

        if not username or not email or not password:
            return jsonify({"error": "Username, email, and password are required"}), 400

        try:
            with get_db() as db:
                user = UserManager.create_user(
                    username=username,
                    email=email,
                    password=password,
                    full_name=full_name,
                    team_id=team_id,
                    role_ids=role_ids,
                    is_active=is_active,
                    db=db,
                )

                AuditLogger.log_from_request(
                    action="user.create",
                    request=request,
                    user=current_user,
                    resource_type="user",
                    resource_id=str(user.id),
                    resource_name=user.username,
                    status="success",
                    db=db,
                )

                return jsonify({
                    "message": "User created successfully",
                    "user": user.to_dict(),
                }), 201

        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            return jsonify({"error": "Failed to create user"}), 500


class UsersGet(ApiHandler):
    """Get user by ID."""

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["GET", "POST"]

    async def process(self, input: Input, request: Request) -> Output:
        """
        Get user details by ID.

        Expected input:
        {
            "user_id": int
        }
        """
        current_user = SessionManager.get_user_from_request(request)

        if not current_user:
            return jsonify({"error": "Authentication required"}), 401

        user_id = input.get("user_id")

        if not user_id:
            return jsonify({"error": "User ID is required"}), 400

        # Users can view their own profile, or need user.read permission
        if current_user.id != int(user_id) and not RBAC.check_permission(current_user, "user.read"):
            return jsonify({"error": "Permission denied"}), 403

        try:
            user = UserManager.get_user_by_id(int(user_id))

            if not user:
                return jsonify({"error": "User not found"}), 404

            return jsonify({"user": user.to_dict()}), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500


class UsersUpdate(ApiHandler):
    """Update user information."""

    async def process(self, input: Input, request: Request) -> Output:
        """
        Update user details.

        Expected input:
        {
            "user_id": int,
            "username": "string" (optional),
            "email": "string" (optional),
            "full_name": "string" (optional),
            "team_id": int (optional),
            "is_active": bool (optional)
        }
        """
        current_user = SessionManager.get_user_from_request(request)

        if not current_user:
            return jsonify({"error": "Authentication required"}), 401

        user_id = input.get("user_id")

        if not user_id:
            return jsonify({"error": "User ID is required"}), 400

        # Users can update their own profile (limited fields), or need user.update permission
        is_self_update = current_user.id == int(user_id)

        if not is_self_update and not RBAC.check_permission(current_user, "user.update"):
            return jsonify({"error": "Permission denied"}), 403

        update_data = {}

        # Fields that users can update for themselves
        self_allowed_fields = ["full_name", "email"]

        # Fields that require user.update permission
        admin_only_fields = ["username", "team_id", "is_active", "is_superuser"]

        for field in self_allowed_fields:
            if field in input:
                update_data[field] = input[field]

        # Only allow admin fields if user has permission
        if not is_self_update:
            for field in admin_only_fields:
                if field in input:
                    update_data[field] = input[field]

        if not update_data:
            return jsonify({"error": "No fields to update"}), 400

        try:
            with get_db() as db:
                user = UserManager.update_user(int(user_id), update_data, db=db)

                if not user:
                    return jsonify({"error": "User not found"}), 404

                AuditLogger.log_from_request(
                    action="user.update",
                    request=request,
                    user=current_user,
                    resource_type="user",
                    resource_id=str(user.id),
                    resource_name=user.username,
                    status="success",
                    details={"updated_fields": list(update_data.keys())},
                    db=db,
                )

                return jsonify({
                    "message": "User updated successfully",
                    "user": user.to_dict(),
                }), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500


class UsersDelete(ApiHandler):
    """Delete a user."""

    async def process(self, input: Input, request: Request) -> Output:
        """
        Delete a user.

        Expected input:
        {
            "user_id": int
        }
        """
        current_user = SessionManager.get_user_from_request(request)

        if not current_user:
            return jsonify({"error": "Authentication required"}), 401

        if not RBAC.check_permission(current_user, "user.delete"):
            return jsonify({"error": "Permission denied"}), 403

        user_id = input.get("user_id")

        if not user_id:
            return jsonify({"error": "User ID is required"}), 400

        # Prevent deleting yourself
        if current_user.id == int(user_id):
            return jsonify({"error": "Cannot delete your own account"}), 400

        try:
            with get_db() as db:
                # Get user before deletion for audit log
                user = UserManager.get_user_by_id(int(user_id), db=db)

                if not user:
                    return jsonify({"error": "User not found"}), 404

                username = user.username

                success = UserManager.delete_user(int(user_id), db=db)

                if not success:
                    return jsonify({"error": "Failed to delete user"}), 500

                AuditLogger.log_from_request(
                    action="user.delete",
                    request=request,
                    user=current_user,
                    resource_type="user",
                    resource_id=str(user_id),
                    resource_name=username,
                    status="success",
                    db=db,
                )

                return jsonify({"message": "User deleted successfully"}), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500


class UsersAssignRole(ApiHandler):
    """Assign a role to a user."""

    async def process(self, input: Input, request: Request) -> Output:
        """
        Assign a role to a user.

        Expected input:
        {
            "user_id": int,
            "role_id": int
        }
        """
        current_user = SessionManager.get_user_from_request(request)

        if not current_user:
            return jsonify({"error": "Authentication required"}), 401

        if not RBAC.check_permission(current_user, "user.manage_roles"):
            return jsonify({"error": "Permission denied"}), 403

        user_id = input.get("user_id")
        role_id = input.get("role_id")

        if not user_id or not role_id:
            return jsonify({"error": "User ID and Role ID are required"}), 400

        try:
            with get_db() as db:
                success = UserManager.assign_role(int(user_id), int(role_id), db=db)

                if not success:
                    return jsonify({"error": "Failed to assign role"}), 400

                user = UserManager.get_user_by_id(int(user_id), db=db)

                AuditLogger.log_from_request(
                    action="user.role_assign",
                    request=request,
                    user=current_user,
                    resource_type="user",
                    resource_id=str(user_id),
                    resource_name=user.username if user else None,
                    status="success",
                    details={"role_id": role_id},
                    db=db,
                )

                return jsonify({"message": "Role assigned successfully"}), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500


class UsersRevokeRole(ApiHandler):
    """Revoke a role from a user."""

    async def process(self, input: Input, request: Request) -> Output:
        """
        Revoke a role from a user.

        Expected input:
        {
            "user_id": int,
            "role_id": int
        }
        """
        current_user = SessionManager.get_user_from_request(request)

        if not current_user:
            return jsonify({"error": "Authentication required"}), 401

        if not RBAC.check_permission(current_user, "user.manage_roles"):
            return jsonify({"error": "Permission denied"}), 403

        user_id = input.get("user_id")
        role_id = input.get("role_id")

        if not user_id or not role_id:
            return jsonify({"error": "User ID and Role ID are required"}), 400

        try:
            with get_db() as db:
                success = UserManager.revoke_role(int(user_id), int(role_id), db=db)

                if not success:
                    return jsonify({"error": "Failed to revoke role"}), 400

                user = UserManager.get_user_by_id(int(user_id), db=db)

                AuditLogger.log_from_request(
                    action="user.role_revoke",
                    request=request,
                    user=current_user,
                    resource_type="user",
                    resource_id=str(user_id),
                    resource_name=user.username if user else None,
                    status="success",
                    details={"role_id": role_id},
                    db=db,
                )

                return jsonify({"message": "Role revoked successfully"}), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500
