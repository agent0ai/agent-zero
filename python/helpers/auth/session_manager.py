"""Session management for multi-user support with JWT."""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
import os
from python.models.user import User
from python.database import get_db


class SessionManager:
    """Manager for user sessions using JWT tokens."""

    # JWT Configuration
    SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-this-in-production")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))

    @classmethod
    def create_access_token(
        cls,
        user_id: int,
        username: str,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create JWT access token.

        Args:
            user_id: User ID
            username: Username
            expires_delta: Optional custom expiration time

        Returns:
            JWT token string
        """
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=cls.ACCESS_TOKEN_EXPIRE_MINUTES)

        payload = {
            "user_id": user_id,
            "username": username,
            "type": "access",
            "exp": expire,
            "iat": datetime.utcnow(),
        }

        return jwt.encode(payload, cls.SECRET_KEY, algorithm=cls.ALGORITHM)

    @classmethod
    def create_refresh_token(
        cls,
        user_id: int,
        username: str,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create JWT refresh token.

        Args:
            user_id: User ID
            username: Username
            expires_delta: Optional custom expiration time

        Returns:
            JWT refresh token string
        """
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=cls.REFRESH_TOKEN_EXPIRE_DAYS)

        payload = {
            "user_id": user_id,
            "username": username,
            "type": "refresh",
            "exp": expire,
            "iat": datetime.utcnow(),
        }

        return jwt.encode(payload, cls.SECRET_KEY, algorithm=cls.ALGORITHM)

    @classmethod
    def create_tokens(cls, user: User) -> Dict[str, str]:
        """
        Create both access and refresh tokens for a user.

        Args:
            user: User object

        Returns:
            Dictionary with access_token and refresh_token
        """
        access_token = cls.create_access_token(user.id, user.username)
        refresh_token = cls.create_refresh_token(user.id, user.username)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": cls.ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # in seconds
        }

    @classmethod
    def verify_token(cls, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify and decode JWT token.

        Args:
            token: JWT token string

        Returns:
            Decoded payload if valid, None otherwise
        """
        try:
            payload = jwt.decode(token, cls.SECRET_KEY, algorithms=[cls.ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    @classmethod
    def get_user_from_token(cls, token: str) -> Optional[User]:
        """
        Get user object from JWT token.

        Args:
            token: JWT token string

        Returns:
            User object if token is valid and user exists, None otherwise
        """
        payload = cls.verify_token(token)
        if not payload:
            return None

        user_id = payload.get("user_id")
        if not user_id:
            return None

        # Get user from database
        with get_db() as db:
            user = db.query(User).filter(User.id == user_id).first()
            return user

    @classmethod
    def refresh_access_token(cls, refresh_token: str) -> Optional[Dict[str, str]]:
        """
        Create new access token from refresh token.

        Args:
            refresh_token: JWT refresh token string

        Returns:
            Dictionary with new access_token if valid, None otherwise
        """
        payload = cls.verify_token(refresh_token)
        if not payload:
            return None

        # Verify it's a refresh token
        if payload.get("type") != "refresh":
            return None

        user_id = payload.get("user_id")
        username = payload.get("username")

        if not user_id or not username:
            return None

        # Verify user still exists and is active
        with get_db() as db:
            user = db.query(User).filter(User.id == user_id).first()
            if not user or not user.is_active:
                return None

        # Create new access token
        access_token = cls.create_access_token(user_id, username)

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": cls.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }

    @classmethod
    def invalidate_token(cls, token: str) -> bool:
        """
        Invalidate a token (for logout).

        Note: In a production system, you'd want to maintain a blacklist
        of invalidated tokens in Redis or similar cache.

        Args:
            token: JWT token string

        Returns:
            True if token was invalidated
        """
        # TODO: Implement token blacklist with Redis
        # For now, we just verify the token exists
        payload = cls.verify_token(token)
        return payload is not None

    @classmethod
    def extract_token_from_header(cls, authorization_header: Optional[str]) -> Optional[str]:
        """
        Extract JWT token from Authorization header.

        Args:
            authorization_header: Authorization header value (e.g., "Bearer <token>")

        Returns:
            Token string if valid format, None otherwise
        """
        if not authorization_header:
            return None

        parts = authorization_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return None

        return parts[1]

    @classmethod
    def get_user_from_request(cls, request) -> Optional[User]:
        """
        Get user from Flask request object.

        Args:
            request: Flask request object

        Returns:
            User object if authenticated, None otherwise
        """
        auth_header = request.headers.get("Authorization")
        token = cls.extract_token_from_header(auth_header)

        if not token:
            return None

        return cls.get_user_from_token(token)


# Context isolation for multi-user sessions
class SessionContext:
    """Context manager for isolating user sessions."""

    _active_sessions: Dict[int, Dict[str, Any]] = {}

    @classmethod
    def create_session(cls, user_id: int, context_data: Dict[str, Any]) -> str:
        """Create a new session context for a user."""
        session_id = f"session_{user_id}_{datetime.utcnow().timestamp()}"

        cls._active_sessions[user_id] = {
            "session_id": session_id,
            "user_id": user_id,
            "created_at": datetime.utcnow(),
            "last_activity": datetime.utcnow(),
            "context_data": context_data,
        }

        return session_id

    @classmethod
    def get_session(cls, user_id: int) -> Optional[Dict[str, Any]]:
        """Get session context for a user."""
        return cls._active_sessions.get(user_id)

    @classmethod
    def update_session(cls, user_id: int, context_data: Dict[str, Any]) -> None:
        """Update session context for a user."""
        if user_id in cls._active_sessions:
            cls._active_sessions[user_id]["context_data"].update(context_data)
            cls._active_sessions[user_id]["last_activity"] = datetime.utcnow()

    @classmethod
    def end_session(cls, user_id: int) -> bool:
        """End session for a user."""
        if user_id in cls._active_sessions:
            del cls._active_sessions[user_id]
            return True
        return False

    @classmethod
    def cleanup_inactive_sessions(cls, max_inactive_minutes: int = 30) -> int:
        """Clean up sessions inactive for more than max_inactive_minutes."""
        now = datetime.utcnow()
        inactive_threshold = timedelta(minutes=max_inactive_minutes)

        inactive_user_ids = []
        for user_id, session in cls._active_sessions.items():
            last_activity = session["last_activity"]
            if now - last_activity > inactive_threshold:
                inactive_user_ids.append(user_id)

        for user_id in inactive_user_ids:
            del cls._active_sessions[user_id]

        return len(inactive_user_ids)

    @classmethod
    def get_active_session_count(cls) -> int:
        """Get count of active sessions."""
        return len(cls._active_sessions)

    @classmethod
    def get_all_sessions(cls) -> Dict[int, Dict[str, Any]]:
        """Get all active sessions (admin only)."""
        return cls._active_sessions.copy()
