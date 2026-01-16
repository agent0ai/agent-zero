"""Role model for RBAC system."""
from datetime import datetime
from typing import List
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Table, ForeignKey
from sqlalchemy.orm import relationship
from python.database import Base


# Association table for many-to-many relationship between roles and permissions
role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", Integer, ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
)


class Role(Base):
    """Role model for grouping permissions."""

    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(String(1000), nullable=True)
    is_system = Column(Boolean, default=False, nullable=False)  # System roles cannot be deleted
    is_active = Column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    permissions = relationship(
        "Permission",
        secondary=role_permissions,
        back_populates="roles",
    )
    users = relationship(
        "User",
        secondary="user_roles",
        back_populates="roles",
    )

    def has_permission(self, permission_name: str) -> bool:
        """Check if role has a specific permission."""
        for permission in self.permissions:
            if permission.name == permission_name:
                return True
        return False

    def add_permission(self, permission: "Permission") -> None:
        """Add a permission to this role."""
        if permission not in self.permissions:
            self.permissions.append(permission)

    def remove_permission(self, permission: "Permission") -> None:
        """Remove a permission from this role."""
        if permission in self.permissions:
            self.permissions.remove(permission)

    def get_permission_names(self) -> List[str]:
        """Get list of permission names assigned to this role."""
        return [perm.name for perm in self.permissions]

    def to_dict(self) -> dict:
        """Convert role to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "is_system": self.is_system,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "permissions": self.get_permission_names(),
            "user_count": len(self.users),
        }

    def __repr__(self) -> str:
        return f"<Role(id={self.id}, name='{self.name}')>"


# Predefined system roles
SYSTEM_ROLES = {
    "admin": {
        "description": "Administrator with full system access",
        "permissions": ["*"],  # All permissions
    },
    "agent_manager": {
        "description": "Can create and manage agents",
        "permissions": [
            "agent.create",
            "agent.read",
            "agent.update",
            "agent.delete",
            "agent.execute",
            "tool.execute",
            "memory.read",
            "memory.write",
            "logs.view",
        ],
    },
    "agent_user": {
        "description": "Can use existing agents",
        "permissions": [
            "agent.read",
            "agent.execute",
            "tool.execute",
            "memory.read",
            "logs.view",
        ],
    },
    "viewer": {
        "description": "Read-only access to agents and logs",
        "permissions": [
            "agent.read",
            "memory.read",
            "logs.view",
        ],
    },
    "tool_manager": {
        "description": "Can create and manage tools",
        "permissions": [
            "tool.create",
            "tool.read",
            "tool.update",
            "tool.delete",
            "tool.execute",
        ],
    },
}
