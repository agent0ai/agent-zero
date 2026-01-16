"""Team model for multi-tenancy and organization management."""
from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.orm import relationship
from python.database import Base


class Team(Base):
    """Team model for multi-tenancy support."""

    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    slug = Column(String(255), unique=True, nullable=False, index=True)

    # Team settings
    is_active = Column(Boolean, default=True, nullable=False)
    max_users = Column(Integer, default=10, nullable=False)
    max_agents = Column(Integer, default=5, nullable=False)

    # Storage quotas (in MB)
    storage_quota = Column(Integer, default=1000, nullable=False)
    storage_used = Column(Integer, default=0, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    users = relationship("User", back_populates="team")

    @property
    def user_count(self) -> int:
        """Get number of users in team."""
        return len(self.users)

    @property
    def is_full(self) -> bool:
        """Check if team has reached max user capacity."""
        return self.user_count >= self.max_users

    @property
    def storage_percentage(self) -> float:
        """Calculate storage usage percentage."""
        if self.storage_quota == 0:
            return 0.0
        return (self.storage_used / self.storage_quota) * 100

    @property
    def has_storage_available(self) -> bool:
        """Check if team has available storage."""
        return self.storage_used < self.storage_quota

    def add_storage_usage(self, size_mb: int) -> bool:
        """
        Add to storage usage.

        Returns:
            bool: True if storage was added, False if quota exceeded
        """
        if self.storage_used + size_mb > self.storage_quota:
            return False
        self.storage_used += size_mb
        return True

    def remove_storage_usage(self, size_mb: int) -> None:
        """Remove from storage usage."""
        self.storage_used = max(0, self.storage_used - size_mb)

    def can_add_user(self) -> bool:
        """Check if team can accept more users."""
        return self.is_active and not self.is_full

    def to_dict(self, include_users: bool = False) -> dict:
        """Convert team to dictionary representation."""
        data = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "slug": self.slug,
            "is_active": self.is_active,
            "max_users": self.max_users,
            "max_agents": self.max_agents,
            "user_count": self.user_count,
            "storage_quota": self.storage_quota,
            "storage_used": self.storage_used,
            "storage_percentage": round(self.storage_percentage, 2),
            "has_storage_available": self.has_storage_available,
            "is_full": self.is_full,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_users:
            data["users"] = [
                {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "full_name": user.full_name,
                    "is_active": user.is_active,
                }
                for user in self.users
            ]

        return data

    def __repr__(self) -> str:
        return f"<Team(id={self.id}, name='{self.name}', slug='{self.slug}')>"
