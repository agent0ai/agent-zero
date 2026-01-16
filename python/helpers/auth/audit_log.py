"""Audit logging system for tracking user actions."""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from python.models.audit_log import AuditLog, AUDIT_ACTIONS
from python.models.user import User
from python.database import get_db
from flask import Request


class AuditLogger:
    """Logger for user actions and system events."""

    @staticmethod
    def log_action(
        action: str,
        user_id: Optional[int] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        resource_name: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        method: Optional[str] = None,
        path: Optional[str] = None,
        status: str = "success",
        status_code: Optional[int] = None,
        error_message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        duration_ms: Optional[int] = None,
        db: Optional[Session] = None
    ) -> AuditLog:
        """
        Log an action to the audit log.

        Args:
            action: Action name (e.g., 'user.login', 'agent.create')
            user_id: ID of user performing the action
            resource_type: Type of resource affected (e.g., 'agent', 'user')
            resource_id: ID of affected resource
            resource_name: Name of affected resource
            ip_address: IP address of request
            user_agent: User agent string
            method: HTTP method
            path: Request path
            status: Status of action (success, failure, error)
            status_code: HTTP status code
            error_message: Error message if action failed
            details: Additional details as JSON
            duration_ms: Duration of action in milliseconds
            db: Database session (optional)

        Returns:
            Created AuditLog object
        """
        use_context_manager = db is None
        if use_context_manager:
            db_context = get_db()
            db = next(db_context)
        else:
            db_context = None

        try:
            log_entry = AuditLog(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                resource_name=resource_name,
                ip_address=ip_address,
                user_agent=user_agent,
                method=method,
                path=path,
                status=status,
                status_code=status_code,
                error_message=error_message,
                details=details,
                duration_ms=duration_ms,
            )

            db.add(log_entry)
            db.commit()
            db.refresh(log_entry)

            return log_entry

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
    def log_from_request(
        action: str,
        request: Request,
        user: Optional[User] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        resource_name: Optional[str] = None,
        status: str = "success",
        status_code: Optional[int] = None,
        error_message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        duration_ms: Optional[int] = None,
        db: Optional[Session] = None
    ) -> AuditLog:
        """
        Log an action from a Flask request object.

        Args:
            action: Action name
            request: Flask request object
            user: User object (optional)
            ... (other parameters same as log_action)

        Returns:
            Created AuditLog object
        """
        return AuditLogger.log_action(
            action=action,
            user_id=user.id if user else None,
            resource_type=resource_type,
            resource_id=resource_id,
            resource_name=resource_name,
            ip_address=request.remote_addr,
            user_agent=request.headers.get("User-Agent"),
            method=request.method,
            path=request.path,
            status=status,
            status_code=status_code,
            error_message=error_message,
            details=details,
            duration_ms=duration_ms,
            db=db,
        )

    @staticmethod
    def get_logs(
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        status: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100,
        db: Optional[Session] = None
    ) -> List[AuditLog]:
        """
        Get audit logs with filtering and pagination.

        Args:
            user_id: Filter by user ID
            action: Filter by action name
            resource_type: Filter by resource type
            status: Filter by status
            start_date: Filter logs after this date
            end_date: Filter logs before this date
            skip: Number of records to skip
            limit: Maximum number of records to return
            db: Database session (optional)

        Returns:
            List of AuditLog objects
        """
        use_context_manager = db is None
        if use_context_manager:
            db_context = get_db()
            db = next(db_context)
        else:
            db_context = None

        try:
            query = db.query(AuditLog)

            # Apply filters
            if user_id is not None:
                query = query.filter(AuditLog.user_id == user_id)

            if action:
                query = query.filter(AuditLog.action == action)

            if resource_type:
                query = query.filter(AuditLog.resource_type == resource_type)

            if status:
                query = query.filter(AuditLog.status == status)

            if start_date:
                query = query.filter(AuditLog.created_at >= start_date)

            if end_date:
                query = query.filter(AuditLog.created_at <= end_date)

            # Order by most recent first
            query = query.order_by(AuditLog.created_at.desc())

            # Apply pagination
            return query.offset(skip).limit(limit).all()

        finally:
            if use_context_manager and db_context:
                try:
                    db_context.__exit__(None, None, None)
                except:
                    pass

    @staticmethod
    def get_user_activity(
        user_id: int,
        days: int = 7,
        db: Optional[Session] = None
    ) -> List[AuditLog]:
        """
        Get recent activity for a user.

        Args:
            user_id: User ID
            days: Number of days to look back
            db: Database session (optional)

        Returns:
            List of AuditLog objects
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        return AuditLogger.get_logs(
            user_id=user_id,
            start_date=start_date,
            limit=1000,
            db=db
        )

    @staticmethod
    def get_failed_logins(
        hours: int = 24,
        ip_address: Optional[str] = None,
        db: Optional[Session] = None
    ) -> List[AuditLog]:
        """
        Get failed login attempts.

        Args:
            hours: Number of hours to look back
            ip_address: Filter by IP address (optional)
            db: Database session (optional)

        Returns:
            List of AuditLog objects for failed logins
        """
        use_context_manager = db is None
        if use_context_manager:
            db_context = get_db()
            db = next(db_context)
        else:
            db_context = None

        try:
            start_date = datetime.utcnow() - timedelta(hours=hours)
            query = db.query(AuditLog).filter(
                and_(
                    AuditLog.action == "auth.login_failed",
                    AuditLog.created_at >= start_date,
                )
            )

            if ip_address:
                query = query.filter(AuditLog.ip_address == ip_address)

            return query.order_by(AuditLog.created_at.desc()).all()

        finally:
            if use_context_manager and db_context:
                try:
                    db_context.__exit__(None, None, None)
                except:
                    pass

    @staticmethod
    def get_statistics(
        user_id: Optional[int] = None,
        days: int = 7,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Get audit log statistics.

        Args:
            user_id: Filter by user ID (optional)
            days: Number of days to look back
            db: Database session (optional)

        Returns:
            Dictionary with statistics
        """
        use_context_manager = db is None
        if use_context_manager:
            db_context = get_db()
            db = next(db_context)
        else:
            db_context = None

        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            query = db.query(AuditLog).filter(AuditLog.created_at >= start_date)

            if user_id:
                query = query.filter(AuditLog.user_id == user_id)

            total_actions = query.count()
            successful_actions = query.filter(AuditLog.status == "success").count()
            failed_actions = query.filter(AuditLog.status == "failure").count()
            error_actions = query.filter(AuditLog.status == "error").count()

            # Get action breakdown
            from sqlalchemy import func
            action_counts = db.query(
                AuditLog.action,
                func.count(AuditLog.id).label("count")
            ).filter(
                AuditLog.created_at >= start_date
            ).group_by(AuditLog.action).all()

            action_breakdown = {action: count for action, count in action_counts}

            return {
                "period_days": days,
                "start_date": start_date.isoformat(),
                "end_date": datetime.utcnow().isoformat(),
                "total_actions": total_actions,
                "successful_actions": successful_actions,
                "failed_actions": failed_actions,
                "error_actions": error_actions,
                "success_rate": round((successful_actions / total_actions * 100) if total_actions > 0 else 0, 2),
                "action_breakdown": action_breakdown,
            }

        finally:
            if use_context_manager and db_context:
                try:
                    db_context.__exit__(None, None, None)
                except:
                    pass

    @staticmethod
    def cleanup_old_logs(days: int = 90, db: Optional[Session] = None) -> int:
        """
        Delete audit logs older than specified days.

        Args:
            days: Delete logs older than this many days
            db: Database session (optional)

        Returns:
            Number of deleted records
        """
        use_context_manager = db is None
        if use_context_manager:
            db_context = get_db()
            db = next(db_context)
        else:
            db_context = None

        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            deleted_count = db.query(AuditLog).filter(
                AuditLog.created_at < cutoff_date
            ).delete()

            db.commit()
            return deleted_count

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


# Decorator for automatic audit logging
def audit_log(action: str, resource_type: Optional[str] = None):
    """
    Decorator to automatically log API endpoint calls.

    Usage:
        @audit_log("agent.create", resource_type="agent")
        async def create_agent(self, input, request):
            ...
    """
    from functools import wraps

    def decorator(func):
        @wraps(func)
        async def wrapper(self, input, request, *args, **kwargs):
            start_time = datetime.utcnow()
            user = getattr(request, "current_user", None)
            status = "success"
            status_code = 200
            error_message = None
            resource_id = None
            resource_name = None

            try:
                # Execute the function
                result = await func(self, input, request, *args, **kwargs)

                # Extract resource info from result if available
                if isinstance(result, dict):
                    resource_id = result.get("id")
                    resource_name = result.get("name")

                return result

            except Exception as e:
                status = "error"
                status_code = 500
                error_message = str(e)
                raise

            finally:
                # Calculate duration
                duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

                # Log the action
                try:
                    AuditLogger.log_from_request(
                        action=action,
                        request=request,
                        user=user,
                        resource_type=resource_type,
                        resource_id=str(resource_id) if resource_id else None,
                        resource_name=resource_name,
                        status=status,
                        status_code=status_code,
                        error_message=error_message,
                        duration_ms=duration_ms,
                    )
                except Exception as log_error:
                    # Don't fail the request if logging fails
                    print(f"Failed to log audit entry: {log_error}")

        return wrapper
    return decorator
