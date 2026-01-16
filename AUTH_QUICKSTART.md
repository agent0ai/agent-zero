# Agent Zero Authentication - Quick Start Guide

## Installation & Setup (5 Minutes)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Initialize Authentication System
```bash
python setup_auth.py
```

This creates:
- ✓ Database tables (SQLite by default)
- ✓ All permissions (agent.*, tool.*, user.*, etc.)
- ✓ Default roles (admin, agent_manager, agent_user, viewer, tool_manager)
- ✓ Default admin user (username: `admin`, password: `admin123`)

### 3. Verify Installation
```bash
# Test the authentication API
curl -X POST http://localhost:50001/api/auth/status
```

## Usage Examples

### Register a New User
```bash
curl -X POST http://localhost:50001/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice",
    "email": "alice@example.com",
    "password": "securepass123",
    "full_name": "Alice Smith"
  }'
```

### Login
```bash
curl -X POST http://localhost:50001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }'
```

Response:
```json
{
  "message": "Login successful",
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@agent-zero.local",
    "roles": ["admin"],
    "permissions": ["*"]
  },
  "access_token": "eyJ0eXAiOiJKV1Qi...",
  "refresh_token": "eyJ0eXAiOiJKV1Qi...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### Use Protected Endpoints
```bash
# Get current user info
curl -X GET http://localhost:50001/api/auth/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# List all users (requires user.read permission)
curl -X POST http://localhost:50001/api/auth/users/list \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"skip": 0, "limit": 10}'
```

## Frontend Integration

### Add to Your React App

```tsx
import { AuthProvider, LoginForm, useAuth } from '@/components/auth';

// Wrap your app
function App() {
  return (
    <AuthProvider>
      <MainApp />
    </AuthProvider>
  );
}

// Use in components
function Dashboard() {
  const { user, isAuthenticated, logout } = useAuth();

  if (!isAuthenticated) {
    return <LoginForm />;
  }

  return (
    <div>
      <h1>Welcome, {user.username}!</h1>
      <button onClick={logout}>Logout</button>
    </div>
  );
}
```

## Default Roles & Permissions

### Admin
- **All permissions** (`*`)
- Full system access

### Agent Manager
- Create, manage, and execute agents
- Execute tools
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
- Create, update, and delete tools
- Execute tools

## Configuration (Optional)

Create `.env` file for custom settings:

```env
# Database (default: SQLite)
DATABASE_URL=sqlite:///./agent_zero.db
# Or PostgreSQL:
# DATABASE_URL=postgresql://user:pass@localhost/agent_zero
# Or MySQL:
# DATABASE_URL=mysql+pymysql://user:pass@localhost/agent_zero

# JWT Settings
JWT_SECRET_KEY=your-super-secret-key-here
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
```

## Running Tests

```bash
pytest tests/test_authentication.py -v
```

## Database Migrations

```bash
# Create migration after model changes
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback one version
alembic downgrade -1
```

## Common Tasks

### Change Admin Password
```bash
curl -X POST http://localhost:50001/api/auth/change-password \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "current_password": "admin123",
    "new_password": "newSecurePassword123"
  }'
```

### Create Custom Role
```bash
curl -X POST http://localhost:50001/api/auth/roles/create \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "data_analyst",
    "description": "Can view and analyze data",
    "permission_ids": [1, 2, 3]
  }'
```

### Assign Role to User
```bash
curl -X POST http://localhost:50001/api/auth/users/assign-role \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 2,
    "role_id": 3
  }'
```

### View Audit Logs
```bash
# Get auth status (includes audit statistics)
curl -X POST http://localhost:50001/api/auth/status \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Security Checklist

- [x] Change default admin password immediately
- [x] Use strong JWT secret in production
- [x] Use HTTPS in production
- [x] Set appropriate token expiration times
- [x] Monitor failed login attempts
- [x] Regular database backups
- [x] Review audit logs periodically

## Troubleshooting

### "Authentication required" error
- Check if token is expired (tokens expire after 60 minutes by default)
- Use refresh token to get a new access token
- Verify Authorization header format: `Bearer <token>`

### Permission denied
- Check user's roles: `GET /api/auth/me`
- Verify required permissions for the endpoint
- Ensure user has an active role assigned

### Database errors
- Check DATABASE_URL in .env
- Run migrations: `alembic upgrade head`
- Verify database is accessible

## Full Documentation

See `docs/AUTHENTICATION.md` for complete documentation including:
- All API endpoints
- Permission system details
- Multi-tenancy features
- Session management
- Audit logging
- Advanced usage

## Need Help?

1. Check logs: `tail -f logs/agent_zero.log`
2. Review audit logs via API
3. Run tests: `pytest tests/test_authentication.py -v`
4. See full docs: `docs/AUTHENTICATION.md`
