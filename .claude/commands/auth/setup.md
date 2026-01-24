---
description: Set up authentication system with JWT, OAuth, or session-based auth
argument-hint: <jwt|oauth|session> [--provider google|github|auth0]
model: claude-sonnet-4-5-20250929
allowed-tools: Task, Write, AskUserQuestion, Bash
---

Set up authentication: **$ARGUMENTS**

## Authentication Strategies

**JWT (JSON Web Tokens)** - Stateless, API-friendly
**OAuth 2.0** - Third-party login (Google, GitHub, etc.)
**Session-based** - Traditional server-side sessions

## Integration Points

**Development Workflow**:

- `/dev/feature-request` → Detects auth requirements
- `/dev/implement` → Routes to auth setup if needed
- `/dev/test` → Generates auth tests automatically

**Security**:

- `/dev/review` → Security audit of auth code
- `/devops/setup` → Configures secrets (JWT keys, OAuth credentials)

## Setup JWT Authentication

Routes to **gcp-security-compliance** for implementation:

```javascript
await Task({
  subagent_type: 'gcp-security-compliance',
  description: 'Implement JWT authentication',
  prompt: `Set up JWT authentication with:

- Token generation and validation
- Refresh token rotation
- Role-based access control (RBAC)
- Secure key storage (Cloud KMS or Secret Manager)
- Token expiry (15min access, 7day refresh)

Generate:
1. Auth middleware
2. Login/logout endpoints
3. Token refresh endpoint
4. Protected route examples
5. Unit tests
6. Security best practices doc
  `
})
```

Creates:

```
src/auth/
├── jwt.ts (token generation/validation)
├── middleware.ts (auth middleware)
├── routes.ts (login, logout, refresh)
├── rbac.ts (role-based access)
└── __tests__/auth.test.ts
```

## Setup OAuth (Google, GitHub, etc.)

```javascript
await Task({
  subagent_type: 'gcp-api-architect',
  description: 'Implement OAuth authentication',
  prompt: `Set up OAuth 2.0 with ${PROVIDER}:

- OAuth flow implementation
- Callback handling
- User profile extraction
- Account linking
- Secure credential storage

Provider: ${PROVIDER}
Scopes: ${SCOPES}
  `
})
```

## Security Checklist

- [ ] Passwords hashed with bcrypt (cost factor ≥ 12)
- [ ] JWTs signed with RS256 (not HS256)
- [ ] Refresh tokens stored securely, rotated on use
- [ ] Rate limiting on login endpoints
- [ ] Account lockout after failed attempts
- [ ] 2FA/MFA supported
- [ ] CSRF protection enabled
- [ ] Secure session cookies (httpOnly, secure, sameSite)

## Commands

**`/auth/setup jwt`** - JWT authentication
**`/auth/setup oauth google`** - OAuth with Google
**`/auth/test`** - Test auth endpoints
**`/auth/rotate-keys`** - Rotate JWT signing keys
**`/auth/audit`** - Security audit of auth system

---
**Uses**: gcp-security-compliance, healthcare-security-compliance
