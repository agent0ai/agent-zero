"""Permission model for fine-grained access control."""
from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import relationship
from python.database import Base


class Permission(Base):
    """Permission model for granular access control."""

    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(String(1000), nullable=True)
    resource = Column(String(255), nullable=False, index=True)  # e.g., "agent", "tool", "memory"
    action = Column(String(255), nullable=False, index=True)  # e.g., "create", "read", "update", "delete"

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    roles = relationship(
        "Role",
        secondary="role_permissions",
        back_populates="permissions",
    )

    def to_dict(self) -> dict:
        """Convert permission to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "resource": self.resource,
            "action": self.action,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<Permission(id={self.id}, name='{self.name}')>"


# Predefined permissions structure
PERMISSIONS_SCHEMA = {
    "agent": {
        "create": "Create new agents",
        "read": "View agent details",
        "update": "Modify agent configuration",
        "delete": "Delete agents",
        "execute": "Execute agent tasks",
    },
    "tool": {
        "create": "Create new tools",
        "read": "View tool details",
        "update": "Modify tool configuration",
        "delete": "Delete tools",
        "execute": "Execute tools",
    },
    "memory": {
        "read": "Read memory entries",
        "write": "Write to memory",
        "delete": "Delete memory entries",
        "export": "Export memory data",
    },
    "settings": {
        "read": "View system settings",
        "write": "Modify system settings",
        "export": "Export settings",
        "import": "Import settings",
    },
    "logs": {
        "view": "View system logs",
        "export": "Export log files",
        "delete": "Delete logs",
    },
    "audit": {
        "view": "View audit logs",
        "export": "Export audit logs",
    },
    "user": {
        "create": "Create new users",
        "read": "View user details",
        "update": "Modify user information",
        "delete": "Delete users",
        "manage_roles": "Assign roles to users",
    },
    "role": {
        "create": "Create new roles",
        "read": "View role details",
        "update": "Modify role permissions",
        "delete": "Delete roles",
    },
    "team": {
        "create": "Create new teams",
        "read": "View team details",
        "update": "Modify team information",
        "delete": "Delete teams",
        "manage_members": "Add/remove team members",
    },
    "chat": {
        "create": "Create new chat sessions",
        "read": "View chat history",
        "update": "Modify chat settings",
        "delete": "Delete chat sessions",
    },
    "file": {
        "upload": "Upload files",
        "download": "Download files",
        "delete": "Delete files",
        "share": "Share files with others",
    },
}


def get_all_permissions() -> list:
    """Generate all permission definitions from schema."""
    permissions = []
    for resource, actions in PERMISSIONS_SCHEMA.items():
        for action, description in actions.items():
            permissions.append({
                "name": f"{resource}.{action}",
                "description": description,
                "resource": resource,
                "action": action,
            })
    return permissions
