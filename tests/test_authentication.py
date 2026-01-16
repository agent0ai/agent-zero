"""
Tests for the authentication and RBAC system.

Run with: pytest tests/test_authentication.py
"""
import pytest
from python.database import init_db, get_db
from python.helpers.auth.user_manager import UserManager
from python.helpers.auth.rbac import RBAC
from python.helpers.auth.session_manager import SessionManager
from python.models.role import Role
from python.models.permission import Permission


@pytest.fixture(scope="function")
def setup_database():
    """Setup test database."""
    # Use in-memory SQLite for testing
    import os
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"

    # Initialize database
    init_db()

    # Initialize permissions and roles
    RBAC.initialize_permissions()
    RBAC.initialize_roles()

    yield

    # Cleanup is automatic with in-memory database


def test_user_creation(setup_database):
    """Test user creation."""
    with get_db() as db:
        user = UserManager.create_user(
            username="testuser",
            email="test@example.com",
            password="testpassword123",
            full_name="Test User",
            db=db
        )

        assert user.id is not None
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.full_name == "Test User"
        assert user.is_active is True
        assert user.verify_password("testpassword123") is True
        assert user.verify_password("wrongpassword") is False


def test_user_authentication(setup_database):
    """Test user authentication."""
    with get_db() as db:
        # Create user
        UserManager.create_user(
            username="testuser",
            email="test@example.com",
            password="testpassword123",
            db=db
        )

        # Test successful authentication
        user = UserManager.authenticate("testuser", "testpassword123", db=db)
        assert user is not None
        assert user.username == "testuser"

        # Test authentication with email
        user = UserManager.authenticate("test@example.com", "testpassword123", db=db)
        assert user is not None

        # Test failed authentication
        user = UserManager.authenticate("testuser", "wrongpassword", db=db)
        assert user is None


def test_role_assignment(setup_database):
    """Test role assignment to users."""
    with get_db() as db:
        # Create user
        user = UserManager.create_user(
            username="testuser",
            email="test@example.com",
            password="testpassword123",
            db=db
        )

        # Get agent_user role
        role = db.query(Role).filter(Role.name == "agent_user").first()
        assert role is not None

        # Assign role
        success = UserManager.assign_role(user.id, role.id, db=db)
        assert success is True

        # Verify role assignment
        user = UserManager.get_user_by_id(user.id, db=db)
        assert len(user.roles) == 1
        assert user.roles[0].name == "agent_user"


def test_permissions(setup_database):
    """Test permission checking."""
    with get_db() as db:
        # Create user with agent_manager role
        role = db.query(Role).filter(Role.name == "agent_manager").first()
        user = UserManager.create_user(
            username="testuser",
            email="test@example.com",
            password="testpassword123",
            role_ids=[role.id],
            db=db
        )

        # Check permissions
        assert user.has_permission("agent.create") is True
        assert user.has_permission("agent.read") is True
        assert user.has_permission("user.delete") is False

        # Test superuser
        admin = UserManager.create_user(
            username="admin",
            email="admin@example.com",
            password="adminpassword",
            is_superuser=True,
            db=db
        )

        # Superuser has all permissions
        assert admin.has_permission("agent.create") is True
        assert admin.has_permission("user.delete") is True
        assert admin.has_permission("any.permission") is True


def test_jwt_token_creation(setup_database):
    """Test JWT token creation and verification."""
    with get_db() as db:
        # Create user
        user = UserManager.create_user(
            username="testuser",
            email="test@example.com",
            password="testpassword123",
            db=db
        )

        # Create tokens
        tokens = SessionManager.create_tokens(user)

        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert "token_type" in tokens
        assert tokens["token_type"] == "bearer"

        # Verify access token
        payload = SessionManager.verify_token(tokens["access_token"])
        assert payload is not None
        assert payload["user_id"] == user.id
        assert payload["username"] == user.username
        assert payload["type"] == "access"

        # Verify refresh token
        payload = SessionManager.verify_token(tokens["refresh_token"])
        assert payload is not None
        assert payload["type"] == "refresh"


def test_user_update(setup_database):
    """Test user update functionality."""
    with get_db() as db:
        # Create user
        user = UserManager.create_user(
            username="testuser",
            email="test@example.com",
            password="testpassword123",
            db=db
        )

        # Update user
        updated_user = UserManager.update_user(
            user.id,
            {
                "full_name": "Updated Name",
                "email": "newemail@example.com"
            },
            db=db
        )

        assert updated_user.full_name == "Updated Name"
        assert updated_user.email == "newemail@example.com"

        # Update password
        updated_user = UserManager.update_user(
            user.id,
            {"password": "newpassword123"},
            db=db
        )

        # Verify new password works
        auth_user = UserManager.authenticate("testuser", "newpassword123", db=db)
        assert auth_user is not None


def test_user_deletion(setup_database):
    """Test user deletion."""
    with get_db() as db:
        # Create user
        user = UserManager.create_user(
            username="testuser",
            email="test@example.com",
            password="testpassword123",
            db=db
        )

        user_id = user.id

        # Delete user
        success = UserManager.delete_user(user_id, db=db)
        assert success is True

        # Verify user is deleted
        deleted_user = UserManager.get_user_by_id(user_id, db=db)
        assert deleted_user is None


def test_list_users(setup_database):
    """Test listing users with filters."""
    with get_db() as db:
        # Create multiple users
        for i in range(5):
            UserManager.create_user(
                username=f"user{i}",
                email=f"user{i}@example.com",
                password="password123",
                is_active=(i % 2 == 0),  # Alternate active/inactive
                db=db
            )

        # List all users
        all_users = UserManager.list_users(db=db)
        assert len(all_users) == 5

        # List active users only
        active_users = UserManager.list_users(is_active=True, db=db)
        assert len(active_users) == 3

        # List with search
        search_users = UserManager.list_users(search="user1", db=db)
        assert len(search_users) == 1
        assert search_users[0].username == "user1"


def test_rbac_operations(setup_database):
    """Test RBAC role and permission operations."""
    with get_db() as db:
        # Create custom role
        role = RBAC.create_role(
            name="custom_role",
            description="Custom test role",
            db=db
        )

        assert role.name == "custom_role"
        assert role.is_system is False

        # Get permission
        permission = db.query(Permission).filter(
            Permission.name == "agent.create"
        ).first()

        # Add permission to role
        success = RBAC.add_permission_to_role(role.id, permission.id, db=db)
        assert success is True

        # Verify permission added
        role = db.query(Role).filter(Role.id == role.id).first()
        assert len(role.permissions) == 1
        assert role.permissions[0].name == "agent.create"

        # Remove permission
        success = RBAC.remove_permission_from_role(role.id, permission.id, db=db)
        assert success is True

        # Verify permission removed
        role = db.query(Role).filter(Role.id == role.id).first()
        assert len(role.permissions) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
