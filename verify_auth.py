#!/usr/bin/env python3
"""
Verification script for Agent Zero authentication system.

This script verifies that the authentication system is properly set up
and all components are working correctly.
"""
import sys
import os
import requests
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from python.helpers.print_style import PrintStyle


def print_header(text):
    """Print a formatted header."""
    style = PrintStyle(
        font_color="cyan",
        background_color="black",
        bold=True,
        padding=True
    )
    style.print(f"\n{'='*60}")
    style.print(text)
    style.print('='*60)


def print_success(text):
    """Print a success message."""
    style = PrintStyle(font_color="green", padding=True)
    style.print(f"✓ {text}")


def print_error(text):
    """Print an error message."""
    style = PrintStyle(font_color="red", padding=True)
    style.print(f"✗ {text}")


def print_info(text):
    """Print an info message."""
    style = PrintStyle(font_color="yellow", padding=True)
    style.print(f"ℹ {text}")


def verify_database():
    """Verify database tables exist."""
    print_header("1. Verifying Database Setup")

    try:
        from python.database import engine
        from python.models.user import User
        from python.models.role import Role
        from python.models.permission import Permission
        from python.models.team import Team
        from python.models.audit_log import AuditLog

        # Check if tables exist
        tables = engine.table_names()

        required_tables = ['users', 'roles', 'permissions', 'teams', 'audit_logs']

        for table in required_tables:
            if table in tables:
                print_success(f"Table '{table}' exists")
            else:
                print_error(f"Table '{table}' missing")
                return False

        return True

    except Exception as e:
        print_error(f"Database verification failed: {str(e)}")
        return False


def verify_permissions():
    """Verify permissions are initialized."""
    print_header("2. Verifying Permissions")

    try:
        from python.database import get_db
        from python.models.permission import Permission

        with get_db() as db:
            count = db.query(Permission).count()

            if count > 0:
                print_success(f"Found {count} permissions")
                return True
            else:
                print_error("No permissions found")
                return False

    except Exception as e:
        print_error(f"Permission verification failed: {str(e)}")
        return False


def verify_roles():
    """Verify default roles exist."""
    print_header("3. Verifying Roles")

    try:
        from python.database import get_db
        from python.models.role import Role

        required_roles = ['admin', 'agent_manager', 'agent_user', 'viewer', 'tool_manager']

        with get_db() as db:
            for role_name in required_roles:
                role = db.query(Role).filter(Role.name == role_name).first()
                if role:
                    print_success(f"Role '{role_name}' exists with {len(role.permissions)} permissions")
                else:
                    print_error(f"Role '{role_name}' missing")
                    return False

        return True

    except Exception as e:
        print_error(f"Role verification failed: {str(e)}")
        return False


def verify_admin_user():
    """Verify admin user exists."""
    print_header("4. Verifying Admin User")

    try:
        from python.database import get_db
        from python.models.user import User

        with get_db() as db:
            admin = db.query(User).filter(User.username == "admin").first()

            if admin:
                print_success(f"Admin user exists (ID: {admin.id})")
                print_success(f"Email: {admin.email}")
                print_success(f"Is superuser: {admin.is_superuser}")
                print_success(f"Is active: {admin.is_active}")
                print_success(f"Roles: {', '.join([r.name for r in admin.roles])}")
                return True
            else:
                print_error("Admin user not found")
                return False

    except Exception as e:
        print_error(f"Admin user verification failed: {str(e)}")
        return False


def verify_api_endpoints(base_url="http://localhost:50001"):
    """Verify API endpoints are accessible."""
    print_header("5. Verifying API Endpoints")

    try:
        # Test auth status endpoint
        response = requests.post(f"{base_url}/api/auth/status", timeout=5)

        if response.status_code == 200:
            data = response.json()
            print_success("Auth status endpoint is accessible")
            print_info(f"Users: {data['statistics']['users']['total']}")
            print_info(f"Roles: {data['statistics']['roles']}")
            print_info(f"Permissions: {data['statistics']['permissions']}")
            return True
        else:
            print_error(f"Auth status endpoint returned {response.status_code}")
            return False

    except requests.exceptions.ConnectionError:
        print_error("Could not connect to API server")
        print_info("Make sure the Agent Zero server is running")
        return False
    except Exception as e:
        print_error(f"API verification failed: {str(e)}")
        return False


def test_authentication(base_url="http://localhost:50001"):
    """Test authentication flow."""
    print_header("6. Testing Authentication Flow")

    try:
        # Test login
        print_info("Testing login with admin credentials...")
        response = requests.post(
            f"{base_url}/api/auth/login",
            json={"username": "admin", "password": "admin123"},
            timeout=5
        )

        if response.status_code != 200:
            print_error(f"Login failed with status {response.status_code}")
            return False

        data = response.json()

        if "access_token" not in data:
            print_error("No access token in response")
            return False

        print_success("Login successful")
        print_success("Access token received")

        access_token = data["access_token"]

        # Test protected endpoint
        print_info("Testing protected endpoint...")
        response = requests.get(
            f"{base_url}/api/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=5
        )

        if response.status_code == 200:
            print_success("Protected endpoint accessible with token")
            user_data = response.json()["user"]
            print_info(f"Logged in as: {user_data['username']}")
            print_info(f"Permissions: {len(user_data['permissions'])}")
            return True
        else:
            print_error(f"Protected endpoint returned {response.status_code}")
            return False

    except Exception as e:
        print_error(f"Authentication test failed: {str(e)}")
        return False


def run_verification():
    """Run all verification checks."""
    print_header("Agent Zero Authentication System Verification")

    checks = [
        ("Database Setup", verify_database),
        ("Permissions", verify_permissions),
        ("Roles", verify_roles),
        ("Admin User", verify_admin_user),
        ("API Endpoints", lambda: verify_api_endpoints()),
        ("Authentication Flow", lambda: test_authentication()),
    ]

    results = []

    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print_error(f"Check failed with exception: {str(e)}")
            results.append((check_name, False))

    # Print summary
    print_header("Verification Summary")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for check_name, result in results:
        if result:
            print_success(f"{check_name}: PASSED")
        else:
            print_error(f"{check_name}: FAILED")

    print("\n")

    if passed == total:
        style = PrintStyle(
            font_color="green",
            background_color="black",
            bold=True,
            padding=True
        )
        style.print(f"✓ All checks passed ({passed}/{total})")
        style.print("Authentication system is ready to use!")
        return True
    else:
        style = PrintStyle(
            font_color="red",
            background_color="black",
            bold=True,
            padding=True
        )
        style.print(f"✗ Some checks failed ({passed}/{total} passed)")
        style.print("Please fix the issues above")
        return False


if __name__ == "__main__":
    success = run_verification()
    sys.exit(0 if success else 1)
