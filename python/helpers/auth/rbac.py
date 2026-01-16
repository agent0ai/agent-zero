"""Role-Based Access Control (RBAC) system."""
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from python.models.user import User
from python.models.role import Role, SYSTEM_ROLES
from python.models.permission import Permission, get_all_permissions
from python.database import get_db
from functools import wraps
from flask import request, jsonify


class RBAC:
    """Role-Based Access Control manager."""

    @staticmethod
    def initialize_permissions(db: Optional[Session] = None) -> None:
        """Initialize all permissions from schema."""
        use_context_manager = db is None
        if use_context_manager:
            db_context = get_db()
            db = next(db_context)
        else:
            db_context = None

        try:
            all_permissions = get_all_permissions()

            for perm_data in all_permissions:
                # Check if permission already exists
                existing = db.query(Permission).filter(
                    Permission.name == perm_data["name"]
                ).first()

                if not existing:
                    permission = Permission(
                        name=perm_data["name"],
                        description=perm_data["description"],
                        resource=perm_data["resource"],
                        action=perm_data["action"],
                    )
                    db.add(permission)

            db.commit()

        except Exception as e:
            if use_context_manager and db_context:
                db.rollback()
            raise e
        finally:
            if use_context_manager and db_context:
                try:
                    db_context.__exit__(None, None, None)
                except:
                    pass

    @staticmethod
    def initialize_roles(db: Optional[Session] = None) -> None:
        """Initialize system roles with their permissions."""
        use_context_manager = db is None
        if use_context_manager:
            db_context = get_db()
            db = next(db_context)
        else:
            db_context = None

        try:
            for role_name, role_data in SYSTEM_ROLES.items():
                # Check if role already exists
                existing_role = db.query(Role).filter(Role.name == role_name).first()

                if not existing_role:
                    role = Role(
                        name=role_name,
                        description=role_data["description"],
                        is_system=True,
                    )
                    db.add(role)
                    db.flush()  # Get role ID
                else:
                    role = existing_role

                # Assign permissions
                if role_data["permissions"][0] == "*":
                    # Admin role gets all permissions
                    all_perms = db.query(Permission).all()
                    role.permissions = all_perms
                else:
                    # Assign specific permissions
                    permissions = db.query(Permission).filter(
                        Permission.name.in_(role_data["permissions"])
                    ).all()
                    role.permissions = permissions

            db.commit()

        except Exception as e:
            if use_context_manager and db_context:
                db.rollback()
            raise e
        finally:
            if use_context_manager and db_context:
                try:
                    db_context.__exit__(None, None, None)
                except:
                    pass

    @staticmethod
    def check_permission(user: User, permission_name: str) -> bool:
        """
        Check if user has a specific permission.

        Args:
            user: User object
            permission_name: Permission name (e.g., 'agent.create')

        Returns:
            True if user has permission, False otherwise
        """
        if not user or not user.is_active:
            return False

        return user.has_permission(permission_name)

    @staticmethod
    def check_any_permission(user: User, permission_names: List[str]) -> bool:
        """Check if user has any of the specified permissions."""
        if not user or not user.is_active:
            return False

        return user.has_any_permission(permission_names)

    @staticmethod
    def check_all_permissions(user: User, permission_names: List[str]) -> bool:
        """Check if user has all of the specified permissions."""
        if not user or not user.is_active:
            return False

        return user.has_all_permissions(permission_names)

    @staticmethod
    def get_user_permissions(user: User) -> List[str]:
        """Get all permissions for a user."""
        if not user or not user.is_active:
            return []

        return user.get_all_permissions()

    @staticmethod
    def create_role(
        name: str,
        description: Optional[str] = None,
        permission_ids: Optional[List[int]] = None,
        db: Optional[Session] = None
    ) -> Role:
        """Create a new role with permissions."""
        use_context_manager = db is None
        if use_context_manager:
            db_context = get_db()
            db = next(db_context)
        else:
            db_context = None

        try:
            # Check if role already exists
            existing = db.query(Role).filter(Role.name == name).first()
            if existing:
                raise ValueError(f"Role '{name}' already exists")

            role = Role(
                name=name,
                description=description,
                is_system=False,
            )

            # Assign permissions if provided
            if permission_ids:
                permissions = db.query(Permission).filter(
                    Permission.id.in_(permission_ids)
                ).all()
                role.permissions = permissions

            db.add(role)
            db.commit()
            db.refresh(role)

            return role

        except Exception as e:
            if use_context_manager and db_context:
                db.rollback()
            raise e
        finally:
            if use_context_manager and db_context:
                try:
                    db_context.__exit__(None, None, None)
                except:
                    pass

    @staticmethod
    def update_role(
        role_id: int,
        update_data: Dict[str, Any],
        db: Optional[Session] = None
    ) -> Optional[Role]:
        """Update role information."""
        use_context_manager = db is None
        if use_context_manager:
            db_context = get_db()
            db = next(db_context)
        else:
            db_context = None

        try:
            role = db.query(Role).filter(Role.id == role_id).first()
            if not role:
                return None

            # Cannot modify system roles
            if role.is_system and "name" in update_data:
                raise ValueError("Cannot modify system role name")

            # Update allowed fields
            allowed_fields = {"description", "is_active"}

            for field, value in update_data.items():
                if field in allowed_fields and hasattr(role, field):
                    setattr(role, field, value)

            db.commit()
            db.refresh(role)

            return role

        except Exception as e:
            if use_context_manager and db_context:
                db.rollback()
            raise e
        finally:
            if use_context_manager and db_context:
                try:
                    db_context.__exit__(None, None, None)
                except:
                    pass

    @staticmethod
    def delete_role(role_id: int, db: Optional[Session] = None) -> bool:
        """Delete a role (system roles cannot be deleted)."""
        use_context_manager = db is None
        if use_context_manager:
            db_context = get_db()
            db = next(db_context)
        else:
            db_context = None

        try:
            role = db.query(Role).filter(Role.id == role_id).first()
            if not role:
                return False

            # Cannot delete system roles
            if role.is_system:
                raise ValueError("Cannot delete system role")

            db.delete(role)
            db.commit()
            return True

        except Exception as e:
            if use_context_manager and db_context:
                db.rollback()
            raise e
        finally:
            if use_context_manager and db_context:
                try:
                    db_context.__exit__(None, None, None)
                except:
                    pass

    @staticmethod
    def add_permission_to_role(
        role_id: int,
        permission_id: int,
        db: Optional[Session] = None
    ) -> bool:
        """Add a permission to a role."""
        use_context_manager = db is None
        if use_context_manager:
            db_context = get_db()
            db = next(db_context)
        else:
            db_context = None

        try:
            role = db.query(Role).filter(Role.id == role_id).first()
            permission = db.query(Permission).filter(Permission.id == permission_id).first()

            if not role or not permission:
                return False

            role.add_permission(permission)
            db.commit()
            return True

        except Exception as e:
            if use_context_manager and db_context:
                db.rollback()
            raise e
        finally:
            if use_context_manager and db_context:
                try:
                    db_context.__exit__(None, None, None)
                except:
                    pass

    @staticmethod
    def remove_permission_from_role(
        role_id: int,
        permission_id: int,
        db: Optional[Session] = None
    ) -> bool:
        """Remove a permission from a role."""
        use_context_manager = db is None
        if use_context_manager:
            db_context = get_db()
            db = next(db_context)
        else:
            db_context = None

        try:
            role = db.query(Role).filter(Role.id == role_id).first()
            permission = db.query(Permission).filter(Permission.id == permission_id).first()

            if not role or not permission:
                return False

            role.remove_permission(permission)
            db.commit()
            return True

        except Exception as e:
            if use_context_manager and db_context:
                db.rollback()
            raise e
        finally:
            if use_context_manager and db_context:
                try:
                    db_context.__exit__(None, None, None)
                except:
                    pass

    @staticmethod
    def list_permissions(db: Optional[Session] = None) -> List[Permission]:
        """List all available permissions."""
        use_context_manager = db is None
        if use_context_manager:
            db_context = get_db()
            db = next(db_context)
        else:
            db_context = None

        try:
            return db.query(Permission).order_by(Permission.resource, Permission.action).all()
        finally:
            if use_context_manager and db_context:
                try:
                    db_context.__exit__(None, None, None)
                except:
                    pass

    @staticmethod
    def list_roles(db: Optional[Session] = None) -> List[Role]:
        """List all roles."""
        use_context_manager = db is None
        if use_context_manager:
            db_context = get_db()
            db = next(db_context)
        else:
            db_context = None

        try:
            return db.query(Role).order_by(Role.name).all()
        finally:
            if use_context_manager and db_context:
                try:
                    db_context.__exit__(None, None, None)
                except:
                    pass


def require_permission(permission_name: str):
    """
    Decorator to require a specific permission for an API endpoint.

    Usage:
        @require_permission("agent.create")
        async def create_agent(self, input, request):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(self, input, request, *args, **kwargs):
            # Get current user from request
            user = getattr(request, "current_user", None)

            if not user:
                return jsonify({"error": "Authentication required"}), 401

            # Check permission
            if not RBAC.check_permission(user, permission_name):
                return jsonify({
                    "error": "Permission denied",
                    "required_permission": permission_name
                }), 403

            return await func(self, input, request, *args, **kwargs)

        return wrapper
    return decorator


def require_any_permission(*permission_names: str):
    """Decorator to require any of the specified permissions."""
    def decorator(func):
        @wraps(func)
        async def wrapper(self, input, request, *args, **kwargs):
            user = getattr(request, "current_user", None)

            if not user:
                return jsonify({"error": "Authentication required"}), 401

            if not RBAC.check_any_permission(user, list(permission_names)):
                return jsonify({
                    "error": "Permission denied",
                    "required_permissions": permission_names
                }), 403

            return await func(self, input, request, *args, **kwargs)

        return wrapper
    return decorator


def require_all_permissions(*permission_names: str):
    """Decorator to require all of the specified permissions."""
    def decorator(func):
        @wraps(func)
        async def wrapper(self, input, request, *args, **kwargs):
            user = getattr(request, "current_user", None)

            if not user:
                return jsonify({"error": "Authentication required"}), 401

            if not RBAC.check_all_permissions(user, list(permission_names)):
                return jsonify({
                    "error": "Permission denied",
                    "required_permissions": permission_names
                }), 403

            return await func(self, input, request, *args, **kwargs)

        return wrapper
    return decorator
