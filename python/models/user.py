"""User model for authentication and authorization."""
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import Boolean, Column, DateTime, Integer, String, ForeignKey, Table
from sqlalchemy.orm import relationship
from python.database import Base
import bcrypt


# Association table for many-to-many relationship between users and roles
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)


class User(Base):
    """User model with authentication and profile information."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)

    # Status fields
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    last_login = Column(DateTime, nullable=True)

    # Foreign keys
    team_id = Column(Integer, ForeignKey("teams.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    team = relationship("Team", back_populates="users")
    roles = relationship("Role", secondary=user_roles, back_populates="users")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password: str) -> None:
        """Hash and set password using bcrypt."""
        salt = bcrypt.gensalt()
        self.hashed_password = bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    def verify_password(self, password: str) -> bool:
        """Verify password against stored hash."""
        return bcrypt.checkpw(
            password.encode("utf-8"),
            self.hashed_password.encode("utf-8")
        )

    def has_permission(self, permission_name: str) -> bool:
        """Check if user has a specific permission through their roles."""
        if self.is_superuser:  # type: ignore[truthy-bool]
            return True

        for role in self.roles:
            if role.has_permission(permission_name):
                return True

        return False

    def has_any_permission(self, permission_names: List[str]) -> bool:
        """Check if user has any of the specified permissions."""
        if self.is_superuser:  # type: ignore[truthy-bool]
            return True

        for permission_name in permission_names:
            if self.has_permission(permission_name):
                return True

        return False

    def has_all_permissions(self, permission_names: List[str]) -> bool:
        """Check if user has all of the specified permissions."""
        if self.is_superuser:  # type: ignore[truthy-bool]
            return True

        for permission_name in permission_names:
            if not self.has_permission(permission_name):
                return False

        return True

    def get_all_permissions(self) -> List[str]:
        """Get all permissions assigned to user through their roles."""
        if self.is_superuser:  # type: ignore[truthy-bool]
            return ["*"]  # Superuser has all permissions

        permissions = set()
        for role in self.roles:
            for permission in role.permissions:
                permissions.add(permission.name)

        return sorted(list(permissions))

    def update_last_login(self) -> None:
        """Update last login timestamp."""
        self.last_login = datetime.now(timezone.utc)

    def to_dict(self, include_sensitive: bool = False) -> dict:
        """Convert user to dictionary representation."""
        data = {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "is_active": self.is_active,
            "is_superuser": self.is_superuser,
            "is_verified": self.is_verified,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "team_id": self.team_id,
            "team": self.team.name if self.team else None,
            "roles": [role.name for role in self.roles],
            "permissions": self.get_all_permissions(),
        }

        if include_sensitive:
            data["hashed_password"] = self.hashed_password

        return data

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"
