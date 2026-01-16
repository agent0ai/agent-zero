#!/usr/bin/env python3
"""
Setup script for Agent Zero authentication system.

This script initializes the authentication system by:
1. Creating database tables
2. Initializing permissions
3. Creating default roles
4. Creating default admin user
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from python.database import init_db, get_db
from python.helpers.auth.rbac import RBAC
from python.helpers.auth.user_manager import UserManager
from python.models.role import Role
from python.helpers.print_style import PrintStyle


def setup_authentication():
    """Initialize the authentication system."""
    print_style = PrintStyle(
        font_color="green",
        background_color="black",
        bold=True,
        padding=True
    )

    try:
        print_style.print("Initializing Agent Zero Authentication System...")

        # Step 1: Create database tables
        print_style.print("Step 1/4: Creating database tables...")
        init_db()
        print_style.print("✓ Database tables created successfully")

        # Step 2: Initialize permissions
        print_style.print("\nStep 2/4: Initializing permissions...")
        with get_db() as db:
            RBAC.initialize_permissions(db=db)
        print_style.print("✓ Permissions initialized successfully")

        # Step 3: Initialize roles
        print_style.print("\nStep 3/4: Creating default roles...")
        with get_db() as db:
            RBAC.initialize_roles(db=db)
        print_style.print("✓ Default roles created successfully")

        # Step 4: Create default admin user
        print_style.print("\nStep 4/4: Creating default admin user...")
        with get_db() as db:
            # Check if admin already exists
            existing_admin = UserManager.get_user_by_username("admin", db=db)

            if existing_admin:
                print_style.print("⚠ Admin user already exists, skipping creation")
            else:
                # Get admin role
                admin_role = db.query(Role).filter(Role.name == "admin").first()

                # Create admin user
                admin_user = UserManager.create_user(
                    username="admin",
                    email="admin@agent-zero.local",
                    password="admin123",
                    full_name="System Administrator",
                    is_superuser=True,
                    is_active=True,
                    role_ids=[admin_role.id] if admin_role else [],
                    db=db,
                )

                print_style.print(f"✓ Admin user created successfully")
                print_style.print(f"  Username: admin")
                print_style.print(f"  Email: admin@agent-zero.local")
                print_style.print(f"  Password: admin123")
                print_style.print(f"  \n  ⚠ IMPORTANT: Change the admin password immediately!")

        # Success summary
        print_style = PrintStyle(
            font_color="cyan",
            background_color="black",
            bold=True,
            padding=True
        )
        print_style.print("\n" + "="*60)
        print_style.print("Authentication System Setup Complete!")
        print_style.print("="*60)

        print_style = PrintStyle(
            font_color="white",
            background_color="black",
            padding=True
        )
        print_style.print("\nNext steps:")
        print_style.print("1. Start the Agent Zero server")
        print_style.print("2. Login with admin credentials")
        print_style.print("3. Change the admin password immediately")
        print_style.print("4. Create additional users and roles as needed")
        print_style.print("\nFor more information, see docs/AUTHENTICATION.md")

        return True

    except Exception as e:
        error_style = PrintStyle(
            font_color="red",
            background_color="black",
            bold=True,
            padding=True
        )
        error_style.print(f"\n✗ Error during setup: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = setup_authentication()
    sys.exit(0 if success else 1)
