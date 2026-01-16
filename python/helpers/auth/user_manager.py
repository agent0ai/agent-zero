"""User management module for CRUD operations."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from python.models.user import User
from python.models.role import Role
from python.models.team import Team
from python.database import get_db


class UserManager:
    """Manager class for user CRUD operations."""

    @staticmethod
    def create_user(
        username: str,
        email: str,
        password: str,
        full_name: Optional[str] = None,
        team_id: Optional[int] = None,
        is_active: bool = True,
        is_superuser: bool = False,
        role_ids: Optional[List[int]] = None,
        db: Optional[Session] = None
    ) -> User:
        """
        Create a new user.

        Args:
            username: Unique username
            email: User email address
            password: Plain text password (will be hashed)
            full_name: User's full name
            team_id: ID of team to assign user to
            is_active: Whether user is active
            is_superuser: Whether user has superuser privileges
            role_ids: List of role IDs to assign to user
            db: Database session (optional)

        Returns:
            Created user object

        Raises:
            ValueError: If username or email already exists
        """
        use_context_manager = db is None
        if use_context_manager:
            db_context = get_db()
            db = next(db_context)
        else:
            db_context = None

        try:
            # Check if username or email already exists
            existing_user = db.query(User).filter(
                or_(User.username == username, User.email == email)
            ).first()

            if existing_user:
                if existing_user.username == username:
                    raise ValueError(f"Username '{username}' already exists")
                else:
                    raise ValueError(f"Email '{email}' already exists")

            # Create new user
            user = User(
                username=username,
                email=email,
                full_name=full_name,
                team_id=team_id,
                is_active=is_active,
                is_superuser=is_superuser,
            )

            # Set password (will be hashed)
            user.set_password(password)

            # Assign roles if provided
            if role_ids:
                roles = db.query(Role).filter(Role.id.in_(role_ids)).all()
                user.roles = roles

            db.add(user)
            db.commit()
            db.refresh(user)

            return user

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
    def get_user_by_id(user_id: int, db: Optional[Session] = None) -> Optional[User]:
        """Get user by ID."""
        use_context_manager = db is None
        if use_context_manager:
            db_context = get_db()
            db = next(db_context)
        else:
            db_context = None

        try:
            return db.query(User).filter(User.id == user_id).first()
        finally:
            if use_context_manager and db_context:
                try:
                    db_context.__exit__(None, None, None)
                except:
                    pass

    @staticmethod
    def get_user_by_username(username: str, db: Optional[Session] = None) -> Optional[User]:
        """Get user by username."""
        use_context_manager = db is None
        if use_context_manager:
            db_context = get_db()
            db = next(db_context)
        else:
            db_context = None

        try:
            return db.query(User).filter(User.username == username).first()
        finally:
            if use_context_manager and db_context:
                try:
                    db_context.__exit__(None, None, None)
                except:
                    pass

    @staticmethod
    def get_user_by_email(email: str, db: Optional[Session] = None) -> Optional[User]:
        """Get user by email."""
        use_context_manager = db is None
        if use_context_manager:
            db_context = get_db()
            db = next(db_context)
        else:
            db_context = None

        try:
            return db.query(User).filter(User.email == email).first()
        finally:
            if use_context_manager and db_context:
                try:
                    db_context.__exit__(None, None, None)
                except:
                    pass

    @staticmethod
    def authenticate(username: str, password: str, db: Optional[Session] = None) -> Optional[User]:
        """
        Authenticate user with username/email and password.

        Args:
            username: Username or email
            password: Plain text password
            db: Database session (optional)

        Returns:
            User object if authentication successful, None otherwise
        """
        use_context_manager = db is None
        if use_context_manager:
            db_context = get_db()
            db = next(db_context)
        else:
            db_context = None

        try:
            # Try to find user by username or email
            user = db.query(User).filter(
                or_(User.username == username, User.email == username)
            ).first()

            if not user:
                return None

            # Verify password
            if not user.verify_password(password):
                return None

            # Check if user is active
            if not user.is_active:
                return None

            # Update last login
            user.update_last_login()
            db.commit()

            return user

        finally:
            if use_context_manager and db_context:
                try:
                    db_context.__exit__(None, None, None)
                except:
                    pass

    @staticmethod
    def update_user(
        user_id: int,
        update_data: Dict[str, Any],
        db: Optional[Session] = None
    ) -> Optional[User]:
        """
        Update user information.

        Args:
            user_id: ID of user to update
            update_data: Dictionary of fields to update
            db: Database session (optional)

        Returns:
            Updated user object or None if not found
        """
        use_context_manager = db is None
        if use_context_manager:
            db_context = get_db()
            db = next(db_context)
        else:
            db_context = None

        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return None

            # Update allowed fields
            allowed_fields = {
                "username", "email", "full_name", "is_active",
                "is_superuser", "is_verified", "team_id"
            }

            for field, value in update_data.items():
                if field in allowed_fields and hasattr(user, field):
                    setattr(user, field, value)

            # Handle password update separately
            if "password" in update_data:
                user.set_password(update_data["password"])

            user.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(user)

            return user

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
    def delete_user(user_id: int, db: Optional[Session] = None) -> bool:
        """
        Delete user by ID.

        Args:
            user_id: ID of user to delete
            db: Database session (optional)

        Returns:
            True if user was deleted, False if not found
        """
        use_context_manager = db is None
        if use_context_manager:
            db_context = get_db()
            db = next(db_context)
        else:
            db_context = None

        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return False

            db.delete(user)
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
    def list_users(
        skip: int = 0,
        limit: int = 100,
        team_id: Optional[int] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        db: Optional[Session] = None
    ) -> List[User]:
        """
        List users with pagination and filtering.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            team_id: Filter by team ID
            is_active: Filter by active status
            search: Search in username, email, or full_name
            db: Database session (optional)

        Returns:
            List of user objects
        """
        use_context_manager = db is None
        if use_context_manager:
            db_context = get_db()
            db = next(db_context)
        else:
            db_context = None

        try:
            query = db.query(User)

            # Apply filters
            if team_id is not None:
                query = query.filter(User.team_id == team_id)

            if is_active is not None:
                query = query.filter(User.is_active == is_active)

            if search:
                search_pattern = f"%{search}%"
                query = query.filter(
                    or_(
                        User.username.ilike(search_pattern),
                        User.email.ilike(search_pattern),
                        User.full_name.ilike(search_pattern),
                    )
                )

            # Apply pagination
            return query.offset(skip).limit(limit).all()

        finally:
            if use_context_manager and db_context:
                try:
                    db_context.__exit__(None, None, None)
                except:
                    pass

    @staticmethod
    def assign_role(user_id: int, role_id: int, db: Optional[Session] = None) -> bool:
        """Assign a role to a user."""
        use_context_manager = db is None
        if use_context_manager:
            db_context = get_db()
            db = next(db_context)
        else:
            db_context = None

        try:
            user = db.query(User).filter(User.id == user_id).first()
            role = db.query(Role).filter(Role.id == role_id).first()

            if not user or not role:
                return False

            if role not in user.roles:
                user.roles.append(role)
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
    def revoke_role(user_id: int, role_id: int, db: Optional[Session] = None) -> bool:
        """Revoke a role from a user."""
        use_context_manager = db is None
        if use_context_manager:
            db_context = get_db()
            db = next(db_context)
        else:
            db_context = None

        try:
            user = db.query(User).filter(User.id == user_id).first()
            role = db.query(Role).filter(Role.id == role_id).first()

            if not user or not role:
                return False

            if role in user.roles:
                user.roles.remove(role)
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
