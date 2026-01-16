"""Role and permission management API endpoints."""
from flask import Request, jsonify
from python.helpers.api import ApiHandler, Input, Output
from python.helpers.auth.session_manager import SessionManager
from python.helpers.auth.audit_log import AuditLogger
from python.helpers.auth.rbac import RBAC
from python.database import get_db


class RolesList(ApiHandler):
    """List all roles."""

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["GET", "POST"]

    async def process(self, input: Input, request: Request) -> Output:
        """List all roles with their permissions."""
        current_user = SessionManager.get_user_from_request(request)

        if not current_user:
            return jsonify({"error": "Authentication required"}), 401

        if not RBAC.check_permission(current_user, "role.read"):
            return jsonify({"error": "Permission denied"}), 403

        try:
            with get_db() as db:
                roles = RBAC.list_roles(db=db)

                return jsonify({
                    "roles": [role.to_dict() for role in roles],
                    "count": len(roles),
                }), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500


class RolesCreate(ApiHandler):
    """Create a new role."""

    async def process(self, input: Input, request: Request) -> Output:
        """
        Create a new role.

        Expected input:
        {
            "name": "string",
            "description": "string" (optional),
            "permission_ids": [int] (optional)
        }
        """
        current_user = SessionManager.get_user_from_request(request)

        if not current_user:
            return jsonify({"error": "Authentication required"}), 401

        if not RBAC.check_permission(current_user, "role.create"):
            return jsonify({"error": "Permission denied"}), 403

        name = input.get("name")
        description = input.get("description")
        permission_ids = input.get("permission_ids")

        if not name:
            return jsonify({"error": "Role name is required"}), 400

        try:
            with get_db() as db:
                role = RBAC.create_role(
                    name=name,
                    description=description,
                    permission_ids=permission_ids,
                    db=db,
                )

                AuditLogger.log_from_request(
                    action="role.create",
                    request=request,
                    user=current_user,
                    resource_type="role",
                    resource_id=str(role.id),
                    resource_name=role.name,
                    status="success",
                    db=db,
                )

                return jsonify({
                    "message": "Role created successfully",
                    "role": role.to_dict(),
                }), 201

        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            return jsonify({"error": "Failed to create role"}), 500


class RolesUpdate(ApiHandler):
    """Update a role."""

    async def process(self, input: Input, request: Request) -> Output:
        """
        Update a role.

        Expected input:
        {
            "role_id": int,
            "description": "string" (optional),
            "is_active": bool (optional)
        }
        """
        current_user = SessionManager.get_user_from_request(request)

        if not current_user:
            return jsonify({"error": "Authentication required"}), 401

        if not RBAC.check_permission(current_user, "role.update"):
            return jsonify({"error": "Permission denied"}), 403

        role_id = input.get("role_id")

        if not role_id:
            return jsonify({"error": "Role ID is required"}), 400

        update_data = {}
        if "description" in input:
            update_data["description"] = input["description"]
        if "is_active" in input:
            update_data["is_active"] = input["is_active"]

        if not update_data:
            return jsonify({"error": "No fields to update"}), 400

        try:
            with get_db() as db:
                role = RBAC.update_role(int(role_id), update_data, db=db)

                if not role:
                    return jsonify({"error": "Role not found"}), 404

                AuditLogger.log_from_request(
                    action="role.update",
                    request=request,
                    user=current_user,
                    resource_type="role",
                    resource_id=str(role.id),
                    resource_name=role.name,
                    status="success",
                    details={"updated_fields": list(update_data.keys())},
                    db=db,
                )

                return jsonify({
                    "message": "Role updated successfully",
                    "role": role.to_dict(),
                }), 200

        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            return jsonify({"error": str(e)}), 500


class RolesDelete(ApiHandler):
    """Delete a role."""

    async def process(self, input: Input, request: Request) -> Output:
        """
        Delete a role.

        Expected input:
        {
            "role_id": int
        }
        """
        current_user = SessionManager.get_user_from_request(request)

        if not current_user:
            return jsonify({"error": "Authentication required"}), 401

        if not RBAC.check_permission(current_user, "role.delete"):
            return jsonify({"error": "Permission denied"}), 403

        role_id = input.get("role_id")

        if not role_id:
            return jsonify({"error": "Role ID is required"}), 400

        try:
            with get_db() as db:
                # Get role before deletion for audit log
                from python.models.role import Role
                role = db.query(Role).filter(Role.id == int(role_id)).first()

                if not role:
                    return jsonify({"error": "Role not found"}), 404

                role_name = role.name

                success = RBAC.delete_role(int(role_id), db=db)

                if not success:
                    return jsonify({"error": "Failed to delete role"}), 500

                AuditLogger.log_from_request(
                    action="role.delete",
                    request=request,
                    user=current_user,
                    resource_type="role",
                    resource_id=str(role_id),
                    resource_name=role_name,
                    status="success",
                    db=db,
                )

                return jsonify({"message": "Role deleted successfully"}), 200

        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            return jsonify({"error": str(e)}), 500


class RolesAddPermission(ApiHandler):
    """Add a permission to a role."""

    async def process(self, input: Input, request: Request) -> Output:
        """
        Add a permission to a role.

        Expected input:
        {
            "role_id": int,
            "permission_id": int
        }
        """
        current_user = SessionManager.get_user_from_request(request)

        if not current_user:
            return jsonify({"error": "Authentication required"}), 401

        if not RBAC.check_permission(current_user, "role.update"):
            return jsonify({"error": "Permission denied"}), 403

        role_id = input.get("role_id")
        permission_id = input.get("permission_id")

        if not role_id or not permission_id:
            return jsonify({"error": "Role ID and Permission ID are required"}), 400

        try:
            with get_db() as db:
                success = RBAC.add_permission_to_role(int(role_id), int(permission_id), db=db)

                if not success:
                    return jsonify({"error": "Failed to add permission"}), 400

                from python.models.role import Role
                role = db.query(Role).filter(Role.id == int(role_id)).first()

                AuditLogger.log_from_request(
                    action="role.permission_add",
                    request=request,
                    user=current_user,
                    resource_type="role",
                    resource_id=str(role_id),
                    resource_name=role.name if role else None,
                    status="success",
                    details={"permission_id": permission_id},
                    db=db,
                )

                return jsonify({"message": "Permission added to role successfully"}), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500


class RolesRemovePermission(ApiHandler):
    """Remove a permission from a role."""

    async def process(self, input: Input, request: Request) -> Output:
        """
        Remove a permission from a role.

        Expected input:
        {
            "role_id": int,
            "permission_id": int
        }
        """
        current_user = SessionManager.get_user_from_request(request)

        if not current_user:
            return jsonify({"error": "Authentication required"}), 401

        if not RBAC.check_permission(current_user, "role.update"):
            return jsonify({"error": "Permission denied"}), 403

        role_id = input.get("role_id")
        permission_id = input.get("permission_id")

        if not role_id or not permission_id:
            return jsonify({"error": "Role ID and Permission ID are required"}), 400

        try:
            with get_db() as db:
                success = RBAC.remove_permission_from_role(int(role_id), int(permission_id), db=db)

                if not success:
                    return jsonify({"error": "Failed to remove permission"}), 400

                from python.models.role import Role
                role = db.query(Role).filter(Role.id == int(role_id)).first()

                AuditLogger.log_from_request(
                    action="role.permission_remove",
                    request=request,
                    user=current_user,
                    resource_type="role",
                    resource_id=str(role_id),
                    resource_name=role.name if role else None,
                    status="success",
                    details={"permission_id": permission_id},
                    db=db,
                )

                return jsonify({"message": "Permission removed from role successfully"}), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500


class PermissionsList(ApiHandler):
    """List all permissions."""

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["GET", "POST"]

    async def process(self, input: Input, request: Request) -> Output:
        """List all available permissions."""
        current_user = SessionManager.get_user_from_request(request)

        if not current_user:
            return jsonify({"error": "Authentication required"}), 401

        if not RBAC.check_permission(current_user, "role.read"):
            return jsonify({"error": "Permission denied"}), 403

        try:
            with get_db() as db:
                permissions = RBAC.list_permissions(db=db)

                # Group permissions by resource
                permissions_by_resource = {}
                for perm in permissions:
                    if perm.resource not in permissions_by_resource:
                        permissions_by_resource[perm.resource] = []
                    permissions_by_resource[perm.resource].append(perm.to_dict())

                return jsonify({
                    "permissions": [perm.to_dict() for perm in permissions],
                    "permissions_by_resource": permissions_by_resource,
                    "count": len(permissions),
                }), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500
