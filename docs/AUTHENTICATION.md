# Agent Zero - Authentication & RBAC System

## Overview

Agent Zero now includes a comprehensive enterprise-ready authentication and Role-Based Access Control (RBAC) system that supports multi-user environments with fine-grained permissions.

## Features

- **JWT-based Authentication**: Secure token-based authentication with access and refresh tokens
- **Role-Based Access Control (RBAC)**: Flexible permission system with predefined roles
- **Multi-Tenancy**: Team/Organization support for isolating users and resources
- **Session Management**: Multi-user session isolation with context tracking
- **Audit Logging**: Complete audit trail of all user actions
- **Password Security**: Bcrypt-based password hashing
- **Database Support**: SQLite, PostgreSQL, and MySQL support via SQLAlchemy
- **Database Migrations**: Alembic-based migration system for schema management

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Initialize the Database

```bash
# Run migrations
alembic upgrade head

# Or initialize directly via API
curl -X POST http://localhost:50001/api/auth/initialize
```

This will:
- Create all database tables
- Initialize permissions
- Create default roles
- Create default admin user (username: `admin`, password: `admin123`)

**IMPORTANT**: Change the admin password immediately after first login!

### 3. Environment Configuration

Create a `.env` file with the following variables:

```env
# Database Configuration (optional - defaults to SQLite)
DATABASE_URL=sqlite:///./agent_zero.db
# DATABASE_URL=postgresql://user:password@localhost/agent_zero
# DATABASE_URL=mysql+pymysql://user:password@localhost/agent_zero

# JWT Configuration
JWT_SECRET_KEY=your-super-secret-key-change-this-in-production
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
```

## API Endpoints

### Authentication

#### Register User
```bash
POST /api/auth/register
Content-Type: application/json

{
  "username": "testuser",
  "email": "test@example.com",
  "password": "securepassword123",
  "full_name": "Test User"
}
```

#### Login
```bash
POST /api/auth/login
Content-Type: application/json

{
  "username": "testuser",
  "password": "securepassword123"
}

# Response:
{
  "message": "Login successful",
  "user": { ... },
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

#### Get Current User
```bash
GET /api/auth/me
Authorization: Bearer <access_token>
```

#### Refresh Token
```bash
POST /api/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

#### Change Password
```bash
POST /api/auth/change-password
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "current_password": "oldpassword",
  "new_password": "newpassword123"
}
```

### User Management

#### List Users
```bash
POST /api/auth/users/list
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "skip": 0,
  "limit": 100,
  "search": "optional search term"
}
```

#### Create User
```bash
POST /api/auth/users/create
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "username": "newuser",
  "email": "newuser@example.com",
  "password": "password123",
  "full_name": "New User",
  "role_ids": [2, 3]
}
```

#### Update User
```bash
POST /api/auth/users/update
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "user_id": 1,
  "full_name": "Updated Name",
  "is_active": true
}
```

#### Delete User
```bash
POST /api/auth/users/delete
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "user_id": 1
}
```

#### Assign Role
```bash
POST /api/auth/users/assign-role
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "user_id": 1,
  "role_id": 2
}
```

### Role Management

#### List Roles
```bash
POST /api/auth/roles/list
Authorization: Bearer <access_token>
```

#### Create Role
```bash
POST /api/auth/roles/create
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": "custom_role",
  "description": "Custom role description",
  "permission_ids": [1, 2, 3]
}
```

#### List Permissions
```bash
POST /api/auth/permissions/list
Authorization: Bearer <access_token>
```

## Permissions System

### Permission Format

Permissions follow the format: `resource.action`

Examples:
- `agent.create` - Create agents
- `agent.read` - View agent details
- `tool.execute` - Execute tools
- `memory.write` - Write to memory
- `user.delete` - Delete users

### Available Permissions

#### Agent Permissions
- `agent.create` - Create new agents
- `agent.read` - View agent details
- `agent.update` - Modify agent configuration
- `agent.delete` - Delete agents
- `agent.execute` - Execute agent tasks

#### Tool Permissions
- `tool.create` - Create new tools
- `tool.read` - View tool details
- `tool.update` - Modify tool configuration
- `tool.delete` - Delete tools
- `tool.execute` - Execute tools

#### Memory Permissions
- `memory.read` - Read memory entries
- `memory.write` - Write to memory
- `memory.delete` - Delete memory entries
- `memory.export` - Export memory data

#### User Management Permissions
- `user.create` - Create new users
- `user.read` - View user details
- `user.update` - Modify user information
- `user.delete` - Delete users
- `user.manage_roles` - Assign/revoke roles

#### Role Management Permissions
- `role.create` - Create new roles
- `role.read` - View role details
- `role.update` - Modify role permissions
- `role.delete` - Delete roles

#### Settings Permissions
- `settings.read` - View system settings
- `settings.write` - Modify system settings

#### Logs & Audit Permissions
- `logs.view` - View system logs
- `audit.view` - View audit logs

## Predefined Roles

### Admin
Full system access with all permissions.

### Agent Manager
- Create and manage agents
- Execute agents and tools
- Read/write memory
- View logs

### Agent User
- View and execute existing agents
- Execute tools
- Read memory
- View logs

### Viewer
- Read-only access to agents, memory, and logs

### Tool Manager
- Create and manage tools
- Execute tools

## Multi-Tenancy (Teams)

Teams provide isolation between different organizations or groups.

### Team Model Features
- User capacity limits
- Storage quotas
- Active/inactive status
- Member management

### Creating Teams
```python
from python.models.team import Team
from python.database import get_db

with get_db() as db:
    team = Team(
        name="Engineering Team",
        slug="engineering",
        max_users=20,
        max_agents=10,
        storage_quota=5000  # MB
    )
    db.add(team)
    db.commit()
```

## Session Management

### Multi-User Session Isolation

Each user session is isolated with its own context:

```python
from python.helpers.auth.session_manager import SessionContext

# Create session
session_id = SessionContext.create_session(user_id, {
    "user_id": user.id,
    "username": user.username,
    "team_id": user.team_id,
})

# Get session
session = SessionContext.get_session(user_id)

# Update session
SessionContext.update_session(user_id, {"key": "value"})

# End session
SessionContext.end_session(user_id)
```

## Audit Logging

All user actions are automatically logged for compliance and security.

### Log Entry Structure
- Action performed
- User who performed it
- Resource affected
- IP address and user agent
- Timestamp
- Status (success/failure)
- Additional details

### Viewing Audit Logs

```python
from python.helpers.auth.audit_log import AuditLogger

# Get recent activity for a user
logs = AuditLogger.get_user_activity(user_id=1, days=7)

# Get failed login attempts
failed_logins = AuditLogger.get_failed_logins(hours=24)

# Get statistics
stats = AuditLogger.get_statistics(days=30)
```

## Using Authentication in Code

### Check Permissions

```python
from python.helpers.auth.rbac import RBAC

# Check single permission
if RBAC.check_permission(user, "agent.create"):
    # User can create agents
    pass

# Check multiple permissions (any)
if RBAC.check_any_permission(user, ["agent.create", "tool.create"]):
    # User can create agents OR tools
    pass

# Check multiple permissions (all)
if RBAC.check_all_permissions(user, ["agent.read", "agent.execute"]):
    # User can both read AND execute agents
    pass
```

### Using Decorators

```python
from python.helpers.auth.rbac import require_permission, require_all_permissions

@require_permission("agent.create")
async def create_agent(self, input, request):
    # Only users with agent.create permission can access this
    pass

@require_all_permissions("agent.read", "agent.execute")
async def execute_agent(self, input, request):
    # Only users with both permissions can access this
    pass
```

## Frontend Integration

### Using React Components

```tsx
import { AuthProvider, useAuth, ProtectedRoute } from '@/components/auth';

// Wrap your app with AuthProvider
function App() {
  return (
    <AuthProvider>
      <YourApp />
    </AuthProvider>
  );
}

// Use authentication in components
function Dashboard() {
  const { user, isAuthenticated, hasPermission, logout } = useAuth();

  if (!isAuthenticated) {
    return <LoginForm />;
  }

  return (
    <div>
      <h1>Welcome, {user.username}!</h1>
      {hasPermission('user.create') && (
        <Button onClick={createUser}>Create User</Button>
      )}
      <Button onClick={logout}>Logout</Button>
    </div>
  );
}

// Protect routes
<ProtectedRoute requiredPermission="admin.access">
  <AdminPanel />
</ProtectedRoute>
```

## Database Migrations

### Creating Migrations

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "Add new field to user table"

# Create empty migration
alembic revision -m "Custom migration"
```

### Applying Migrations

```bash
# Upgrade to latest
alembic upgrade head

# Upgrade one version
alembic upgrade +1

# Downgrade one version
alembic downgrade -1
```

### Migration History

```bash
# View current version
alembic current

# View history
alembic history --verbose
```

## Security Best Practices

1. **Change Default Admin Password**: Immediately change the default admin password after initialization
2. **Use Strong JWT Secret**: Set a long, random `JWT_SECRET_KEY` in production
3. **Use HTTPS**: Always use HTTPS in production to protect tokens in transit
4. **Set Short Token Expiration**: Use short access token expiration (60 minutes)
5. **Rotate Secrets**: Periodically rotate JWT secrets
6. **Monitor Failed Logins**: Set up alerts for repeated failed login attempts
7. **Use Database Backups**: Regularly backup your database
8. **Enable Audit Logging**: Keep audit logs for compliance
9. **Use Strong Passwords**: Enforce strong password policies (minimum 8 characters)
10. **Implement Rate Limiting**: Add rate limiting to authentication endpoints

## Troubleshooting

### Database Connection Issues

```bash
# Check database URL
echo $DATABASE_URL

# Test connection
python -c "from python.database import engine; print(engine.execute('SELECT 1').fetchall())"
```

### Token Expiration

If tokens expire too quickly, adjust in `.env`:
```env
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=120
```

### Permission Denied

Check user's roles and permissions:
```bash
curl -H "Authorization: Bearer <token>" http://localhost:50001/api/auth/me
```

## Support

For issues or questions:
1. Check the documentation
2. Review audit logs for errors
3. Check database migrations are up to date
4. Verify environment variables are set correctly
