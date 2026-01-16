"""Authentication middleware for Flask application."""
from functools import wraps
from flask import request, jsonify, g
from python.helpers.auth.session_manager import SessionManager
from python.helpers.auth.rbac import RBAC
from python.helpers.auth.audit_log import AuditLogger


def require_auth(func):
    """Decorator to require authentication for a route."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Get user from request
        user = SessionManager.get_user_from_request(request)

        if not user:
            return jsonify({"error": "Authentication required"}), 401

        if not user.is_active:
            return jsonify({"error": "Account is inactive"}), 403

        # Store user in request context
        request.current_user = user
        g.current_user = user

        return func(*args, **kwargs)

    return wrapper


def require_permission(permission: str):
    """Decorator to require a specific permission."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # First check authentication
            user = getattr(request, 'current_user', None)

            if not user:
                user = SessionManager.get_user_from_request(request)

            if not user:
                return jsonify({"error": "Authentication required"}), 401

            # Check permission
            if not RBAC.check_permission(user, permission):
                # Log permission denied
                AuditLogger.log_from_request(
                    action=f"permission.denied",
                    request=request,
                    user=user,
                    status="failure",
                    error_message=f"Missing permission: {permission}",
                )

                return jsonify({
                    "error": "Permission denied",
                    "required_permission": permission
                }), 403

            # Store user in request context
            request.current_user = user
            g.current_user = user

            return func(*args, **kwargs)

        return wrapper
    return decorator


def optional_auth(func):
    """Decorator that adds user to request if authenticated, but doesn't require it."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Try to get user from request
        user = SessionManager.get_user_from_request(request)

        if user and user.is_active:
            request.current_user = user
            g.current_user = user
        else:
            request.current_user = None
            g.current_user = None

        return func(*args, **kwargs)

    return wrapper


def get_current_user():
    """Get the current authenticated user from request context."""
    return getattr(g, 'current_user', None) or getattr(request, 'current_user', None)


def register_auth_routes(app):
    """Register authentication routes with Flask app."""
    from python.api.auth import (
        AuthRegister,
        AuthLogin,
        AuthLogout,
        AuthRefresh,
        AuthMe,
        AuthChangePassword,
        AuthInitialize,
        AuthStatus,
    )
    from python.api.auth_users import (
        UsersList,
        UsersCreate,
        UsersGet,
        UsersUpdate,
        UsersDelete,
        UsersAssignRole,
        UsersRevokeRole,
    )
    from python.api.auth_roles import (
        RolesList,
        RolesCreate,
        RolesUpdate,
        RolesDelete,
        RolesAddPermission,
        RolesRemovePermission,
        PermissionsList,
    )

    # Authentication routes
    routes = {
        '/api/auth/register': AuthRegister,
        '/api/auth/login': AuthLogin,
        '/api/auth/logout': AuthLogout,
        '/api/auth/refresh': AuthRefresh,
        '/api/auth/me': AuthMe,
        '/api/auth/change-password': AuthChangePassword,
        '/api/auth/initialize': AuthInitialize,
        '/api/auth/status': AuthStatus,
        # User management routes
        '/api/auth/users/list': UsersList,
        '/api/auth/users/create': UsersCreate,
        '/api/auth/users/get': UsersGet,
        '/api/auth/users/update': UsersUpdate,
        '/api/auth/users/delete': UsersDelete,
        '/api/auth/users/assign-role': UsersAssignRole,
        '/api/auth/users/revoke-role': UsersRevokeRole,
        # Role management routes
        '/api/auth/roles/list': RolesList,
        '/api/auth/roles/create': RolesCreate,
        '/api/auth/roles/update': RolesUpdate,
        '/api/auth/roles/delete': RolesDelete,
        '/api/auth/roles/add-permission': RolesAddPermission,
        '/api/auth/roles/remove-permission': RolesRemovePermission,
        '/api/auth/permissions/list': PermissionsList,
    }

    import threading
    thread_lock = threading.Lock()

    for route, handler_class in routes.items():
        handler = handler_class(app, thread_lock)

        # Register route with appropriate methods
        methods = handler_class.get_methods()

        @app.route(route, methods=methods, endpoint=route)
        async def route_handler(handler=handler):
            return await handler.handle_request(request)

    return app
