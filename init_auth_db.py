#!/usr/bin/env python3
"""Initialize authentication database tables and create default data."""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from python.database import Base, engine, get_db, init_db
from python.models.user import User
from python.models.role import Role
from python.models.permission import Permission
from python.models.team import Team
from python.models.audit_log import AuditLog

print("Creating database tables...")
try:
    # Create all tables
    init_db()
    print("✓ Database tables created successfully")

    # Create default permissions, roles, and admin user
    with get_db() as db:
        print("\nCreating default permissions...")

        # Define default permissions
        default_permissions = [
            # Agent permissions
            ("agent.create", "Create new agents", "agent", "create"),
            ("agent.read", "View agent details", "agent", "read"),
            ("agent.update", "Modify agent settings", "agent", "update"),
            ("agent.delete", "Delete agents", "agent", "delete"),
            ("agent.execute", "Execute agent actions", "agent", "execute"),

            # Tool permissions
            ("tool.execute", "Execute tools", "tool", "execute"),
            ("tool.create", "Create custom tools", "tool", "create"),
            ("tool.update", "Modify tools", "tool", "update"),
            ("tool.delete", "Delete tools", "tool", "delete"),

            # Memory permissions
            ("memory.read", "Read memory entries", "memory", "read"),
            ("memory.write", "Write memory entries", "memory", "write"),
            ("memory.delete", "Delete memory entries", "memory", "delete"),

            # Settings permissions
            ("settings.read", "View settings", "settings", "read"),
            ("settings.write", "Modify settings", "settings", "write"),

            # Logs and audit permissions
            ("logs.view", "View system logs", "logs", "view"),
            ("audit.view", "View audit logs", "audit", "view"),

            # User management permissions
            ("user.create", "Create users", "user", "create"),
            ("user.read", "View users", "user", "read"),
            ("user.update", "Modify users", "user", "update"),
            ("user.delete", "Delete users", "user", "delete"),

            # Role management permissions
            ("role.create", "Create roles", "role", "create"),
            ("role.read", "View roles", "role", "read"),
            ("role.update", "Modify roles", "role", "update"),
            ("role.delete", "Delete roles", "role", "delete"),
        ]

        permissions_dict = {}
        for name, description, resource, action in default_permissions:
            perm = db.query(Permission).filter_by(name=name).first()
            if not perm:
                perm = Permission(
                    name=name,
                    description=description,
                    resource=resource,
                    action=action
                )
                db.add(perm)
                permissions_dict[name] = perm
                print(f"  + Created permission: {name}")
            else:
                permissions_dict[name] = perm

        db.commit()
        print(f"✓ Created {len(default_permissions)} permissions")

        print("\nCreating default roles...")

        # Define default roles with their permissions
        default_roles = {
            "admin": {
                "description": "Full system access",
                "permissions": [p[0] for p in default_permissions],  # All permissions
                "is_system": True
            },
            "agent_manager": {
                "description": "Manage agents and execute tasks",
                "permissions": [
                    "agent.create", "agent.read", "agent.update", "agent.delete", "agent.execute",
                    "tool.execute", "memory.read", "memory.write", "logs.view"
                ],
                "is_system": True
            },
            "agent_user": {
                "description": "Execute agents and use tools",
                "permissions": [
                    "agent.read", "agent.execute", "tool.execute",
                    "memory.read", "logs.view"
                ],
                "is_system": True
            },
            "viewer": {
                "description": "Read-only access",
                "permissions": [
                    "agent.read", "tool.execute", "memory.read",
                    "settings.read", "logs.view"
                ],
                "is_system": True
            },
            "tool_manager": {
                "description": "Manage tools and extensions",
                "permissions": [
                    "tool.execute", "tool.create", "tool.update", "tool.delete",
                    "agent.read", "memory.read", "logs.view"
                ],
                "is_system": True
            }
        }

        for role_name, role_data in default_roles.items():
            role = db.query(Role).filter_by(name=role_name).first()
            if not role:
                role = Role(
                    name=role_name,
                    description=role_data["description"],
                    is_system=role_data["is_system"]
                )
                db.add(role)
                db.commit()

                # Add permissions to role
                for perm_name in role_data["permissions"]:
                    if perm_name in permissions_dict:
                        role.permissions.append(permissions_dict[perm_name])

                db.commit()
                print(f"  + Created role: {role_name} with {len(role_data['permissions'])} permissions")

        print(f"✓ Created {len(default_roles)} roles")

        print("\nCreating default admin user...")

        # Create admin user if doesn't exist
        admin = db.query(User).filter_by(username="admin").first()
        if not admin:
            admin = User(
                username="admin",
                email="admin@agent-zero.local",
                full_name="System Administrator",
                is_active=True,
                is_superuser=True,
                is_verified=True
            )
            admin.set_password("admin123")

            # Add admin role
            admin_role = db.query(Role).filter_by(name="admin").first()
            if admin_role:
                admin.roles.append(admin_role)

            db.add(admin)
            db.commit()

            print(f"  + Created admin user")
            print(f"    Username: admin")
            print(f"    Password: admin123")
            print(f"    ⚠ Please change the default password!")
        else:
            print(f"  ℹ Admin user already exists")

        print("\n✓ Database initialization complete!")

except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
