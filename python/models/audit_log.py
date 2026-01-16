"""Audit log model for tracking user actions."""
from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from python.database import Base


class AuditLog(Base):
    """Audit log model for tracking user actions and system events."""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Action details
    action = Column(String(255), nullable=False, index=True)  # e.g., "user.login", "agent.create"
    resource_type = Column(String(255), nullable=True, index=True)  # e.g., "user", "agent", "tool"
    resource_id = Column(String(255), nullable=True, index=True)  # ID of affected resource
    resource_name = Column(String(255), nullable=True)  # Name of affected resource

    # Request details
    ip_address = Column(String(45), nullable=True)  # Support IPv6
    user_agent = Column(String(1000), nullable=True)
    method = Column(String(10), nullable=True)  # HTTP method
    path = Column(String(1000), nullable=True)  # Request path

    # Status and result
    status = Column(String(50), nullable=False, default="success")  # success, failure, error
    status_code = Column(Integer, nullable=True)  # HTTP status code
    error_message = Column(Text, nullable=True)

    # Additional data
    details = Column(JSON, nullable=True)  # Store additional context as JSON
    duration_ms = Column(Integer, nullable=True)  # Request duration in milliseconds

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    user = relationship("User", back_populates="audit_logs")

    def to_dict(self) -> dict:
        """Convert audit log to dictionary representation."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "username": self.user.username if self.user else None,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "resource_name": self.resource_name,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "method": self.method,
            "path": self.path,
            "status": self.status,
            "status_code": self.status_code,
            "error_message": self.error_message,
            "details": self.details,
            "duration_ms": self.duration_ms,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, action='{self.action}', user_id={self.user_id}, status='{self.status}')>"


# Predefined audit action types
AUDIT_ACTIONS = {
    # Authentication
    "auth.login": "User logged in",
    "auth.logout": "User logged out",
    "auth.login_failed": "Login attempt failed",
    "auth.password_change": "User changed password",
    "auth.password_reset": "User reset password",

    # User management
    "user.create": "User created",
    "user.update": "User updated",
    "user.delete": "User deleted",
    "user.activate": "User activated",
    "user.deactivate": "User deactivated",
    "user.role_assign": "Role assigned to user",
    "user.role_revoke": "Role revoked from user",

    # Agent operations
    "agent.create": "Agent created",
    "agent.update": "Agent updated",
    "agent.delete": "Agent deleted",
    "agent.execute": "Agent executed",
    "agent.pause": "Agent paused",
    "agent.resume": "Agent resumed",

    # Tool operations
    "tool.create": "Tool created",
    "tool.update": "Tool updated",
    "tool.delete": "Tool deleted",
    "tool.execute": "Tool executed",

    # Memory operations
    "memory.read": "Memory accessed",
    "memory.write": "Memory written",
    "memory.delete": "Memory deleted",
    "memory.export": "Memory exported",

    # Settings
    "settings.read": "Settings viewed",
    "settings.update": "Settings updated",
    "settings.export": "Settings exported",
    "settings.import": "Settings imported",

    # Team operations
    "team.create": "Team created",
    "team.update": "Team updated",
    "team.delete": "Team deleted",
    "team.member_add": "Member added to team",
    "team.member_remove": "Member removed from team",

    # Role operations
    "role.create": "Role created",
    "role.update": "Role updated",
    "role.delete": "Role deleted",
    "role.permission_add": "Permission added to role",
    "role.permission_remove": "Permission removed from role",

    # Chat operations
    "chat.create": "Chat session created",
    "chat.update": "Chat session updated",
    "chat.delete": "Chat session deleted",
    "chat.message": "Chat message sent",

    # File operations
    "file.upload": "File uploaded",
    "file.download": "File downloaded",
    "file.delete": "File deleted",
    "file.share": "File shared",
}
