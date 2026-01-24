---
description: Test authentication system with comprehensive security validation
argument-hint: [--endpoint login|logout|refresh|protected] [--coverage]
model: claude-sonnet-4-5-20250929
allowed-tools: Bash, Task, Write, AskUserQuestion
---

Test authentication: **${ARGUMENTS}**

## Testing Strategies

**Endpoint Testing** - Test login, logout, refresh token, protected routes
**Security Testing** - Test for common vulnerabilities (XSS, CSRF, injection)
**Performance Testing** - Test under load (concurrent logins, token validation)
**Integration Testing** - Test with frontend and other services
**Compliance Testing** - Verify compliance with security standards

## Integration Points

**Development Workflow**:

- `/auth/setup` → Automatically generates auth tests
- `/dev/test` → Includes auth tests in test suite
- `/dev/review` → Validates auth test coverage

**Deployment Workflow**:

- `/devops/deploy` → Runs auth tests before deployment
- `/devops/monitor` → Monitors auth failures in production

## Test Authentication System

Routes to **gcp-security-compliance** for comprehensive testing:

```javascript
await Task({
  subagent_type: 'gcp-security-compliance',
  description: 'Test authentication system',
  prompt: `Test authentication system endpoints: ${ENDPOINTS || 'all'}

Generate comprehensive authentication tests:

1. **Login Endpoint Tests**:
   ✓ Successful login with valid credentials
   ✓ Login failure with invalid email
   ✓ Login failure with invalid password
   ✓ Login failure with missing fields
   ✓ Rate limiting on failed login attempts
   ✓ Account lockout after N failed attempts
   ✓ Password hash strength (bcrypt cost factor ≥ 12)
   ✓ Response time (should be < 500ms)

2. **Token Generation Tests**:
   ✓ Access token generated with correct claims
   ✓ Refresh token generated and stored
   ✓ Token expiry times correct (15min access, 7d refresh)
   ✓ Token signature algorithm (RS256, not HS256)
   ✓ JWT header includes proper algorithm
   ✓ Token includes required claims (sub, exp, iat)

3. **Token Validation Tests**:
   ✓ Valid token grants access
   ✓ Expired token is rejected
   ✓ Invalid signature is rejected
   ✓ Tampered token is rejected
   ✓ Missing token returns 401
   ✓ Malformed token returns 401

4. **Refresh Token Tests**:
   ✓ Refresh token generates new access token
   ✓ Refresh token is rotated on use
   ✓ Old refresh token is invalidated
   ✓ Expired refresh token is rejected
   ✓ Invalid refresh token is rejected

5. **Logout Tests**:
   ✓ Logout invalidates refresh token
   ✓ Logout with valid token succeeds
   ✓ Logout without token returns 401

6. **Protected Route Tests**:
   ✓ Access with valid token succeeds
   ✓ Access without token returns 401
   ✓ Access with expired token returns 401
   ✓ Access with invalid token returns 401
   ✓ RBAC: User with correct role can access
   ✓ RBAC: User without role is forbidden (403)

7. **Security Tests**:
   ✓ No SQL injection in login (test with: ' OR '1'='1)
   ✓ No XSS in error messages (test with: <script>alert(1)</script>)
   ✓ CSRF protection enabled (test without CSRF token)
   ✓ Password not returned in responses
   ✓ Sensitive data not logged
   ✓ HTTPS only (no plain HTTP)

8. **Performance Tests**:
   ✓ Concurrent logins (100 users)
   ✓ Token validation latency (< 10ms)
   ✓ Database connection pool handling

${COVERAGE ? `
9. **Test Coverage**:
   - Calculate coverage % for auth code
   - Identify untested edge cases
   - Generate missing tests
` : ''}

Generate test files and execute tests.
Provide test results summary with pass/fail counts.
  `
})
```

## Example Auth Test Suite

```javascript
// tests/auth.test.js
const request = require('supertest');
const app = require('../src/app');
const jwt = require('jsonwebtoken');

describe('Authentication System', () => {

  describe('POST /auth/login', () => {
    it('should login with valid credentials', async () => {
      const res = await request(app)
        .post('/auth/login')
        .send({
          email: 'test@example.com',
          password: 'ValidPassword123!'
        });

      expect(res.status).toBe(200);
      expect(res.body).toHaveProperty('accessToken');
      expect(res.body).toHaveProperty('refreshToken');
      expect(res.body.user).toHaveProperty('email', 'test@example.com');
      expect(res.body.user).not.toHaveProperty('password');
    });

    it('should fail with invalid email', async () => {
      const res = await request(app)
        .post('/auth/login')
        .send({
          email: 'wrong@example.com',
          password: 'ValidPassword123!'
        });

      expect(res.status).toBe(401);
      expect(res.body.error).toBe('Invalid credentials');
    });

    it('should fail with invalid password', async () => {
      const res = await request(app)
        .post('/auth/login')
        .send({
          email: 'test@example.com',
          password: 'WrongPassword'
        });

      expect(res.status).toBe(401);
      expect(res.body.error).toBe('Invalid credentials');
    });

    it('should fail with missing fields', async () => {
      const res = await request(app)
        .post('/auth/login')
        .send({ email: 'test@example.com' });

      expect(res.status).toBe(400);
      expect(res.body.error).toMatch(/password.*required/i);
    });

    it('should rate limit failed login attempts', async () => {
      // Make 5 failed login attempts
      for (let i = 0; i < 5; i++) {
        await request(app)
          .post('/auth/login')
          .send({ email: 'test@example.com', password: 'wrong' });
      }

      // 6th attempt should be rate limited
      const res = await request(app)
        .post('/auth/login')
        .send({ email: 'test@example.com', password: 'wrong' });

      expect(res.status).toBe(429);
      expect(res.body.error).toMatch(/too many attempts/i);
    });

    it('should not be vulnerable to SQL injection', async () => {
      const res = await request(app)
        .post('/auth/login')
        .send({
          email: "admin' OR '1'='1",
          password: "anything"
        });

      expect(res.status).toBe(401);
      expect(res.body.error).toBe('Invalid credentials');
    });

    it('should complete within 500ms', async () => {
      const start = Date.now();

      await request(app)
        .post('/auth/login')
        .send({
          email: 'test@example.com',
          password: 'ValidPassword123!'
        });

      const duration = Date.now() - start;
      expect(duration).toBeLessThan(500);
    });
  });

  describe('Token Validation', () => {
    let accessToken;
    let refreshToken;

    beforeEach(async () => {
      const res = await request(app)
        .post('/auth/login')
        .send({
          email: 'test@example.com',
          password: 'ValidPassword123!'
        });

      accessToken = res.body.accessToken;
      refreshToken = res.body.refreshToken;
    });

    it('should validate correct token structure', () => {
      const decoded = jwt.decode(accessToken, { complete: true });

      expect(decoded.header.alg).toBe('RS256');
      expect(decoded.payload).toHaveProperty('sub');
      expect(decoded.payload).toHaveProperty('exp');
      expect(decoded.payload).toHaveProperty('iat');
    });

    it('should reject expired token', async () => {
      // Create expired token
      const expiredToken = jwt.sign(
        { sub: '123', exp: Math.floor(Date.now() / 1000) - 60 },
        process.env.JWT_PRIVATE_KEY,
        { algorithm: 'RS256' }
      );

      const res = await request(app)
        .get('/api/protected')
        .set('Authorization', `Bearer ${expiredToken}`);

      expect(res.status).toBe(401);
      expect(res.body.error).toMatch(/expired/i);
    });

    it('should reject tampered token', async () => {
      const tampered = accessToken.slice(0, -5) + 'XXXXX';

      const res = await request(app)
        .get('/api/protected')
        .set('Authorization', `Bearer ${tampered}`);

      expect(res.status).toBe(401);
      expect(res.body.error).toMatch(/invalid/i);
    });

    it('should reject token with wrong algorithm', async () => {
      // Try to create token with HS256 instead of RS256
      const wrongAlg = jwt.sign(
        { sub: '123' },
        'secret',
        { algorithm: 'HS256' }
      );

      const res = await request(app)
        .get('/api/protected')
        .set('Authorization', `Bearer ${wrongAlg}`);

      expect(res.status).toBe(401);
    });
  });

  describe('POST /auth/refresh', () => {
    let refreshToken;

    beforeEach(async () => {
      const res = await request(app)
        .post('/auth/login')
        .send({
          email: 'test@example.com',
          password: 'ValidPassword123!'
        });

      refreshToken = res.body.refreshToken;
    });

    it('should generate new access token', async () => {
      const res = await request(app)
        .post('/auth/refresh')
        .send({ refreshToken });

      expect(res.status).toBe(200);
      expect(res.body).toHaveProperty('accessToken');
      expect(res.body).toHaveProperty('refreshToken');
      expect(res.body.refreshToken).not.toBe(refreshToken); // Rotated
    });

    it('should invalidate old refresh token', async () => {
      // Use refresh token once
      await request(app)
        .post('/auth/refresh')
        .send({ refreshToken });

      // Try to use old refresh token again
      const res = await request(app)
        .post('/auth/refresh')
        .send({ refreshToken });

      expect(res.status).toBe(401);
      expect(res.body.error).toMatch(/invalid.*refresh.*token/i);
    });

    it('should reject invalid refresh token', async () => {
      const res = await request(app)
        .post('/auth/refresh')
        .send({ refreshToken: 'invalid-token' });

      expect(res.status).toBe(401);
    });
  });

  describe('POST /auth/logout', () => {
    let accessToken;

    beforeEach(async () => {
      const res = await request(app)
        .post('/auth/login')
        .send({
          email: 'test@example.com',
          password: 'ValidPassword123!'
        });

      accessToken = res.body.accessToken;
    });

    it('should logout successfully', async () => {
      const res = await request(app)
        .post('/auth/logout')
        .set('Authorization', `Bearer ${accessToken}`);

      expect(res.status).toBe(200);
      expect(res.body.message).toMatch(/logout.*success/i);
    });

    it('should invalidate refresh token', async () => {
      const loginRes = await request(app)
        .post('/auth/login')
        .send({
          email: 'test@example.com',
          password: 'ValidPassword123!'
        });

      const { refreshToken } = loginRes.body;

      // Logout
      await request(app)
        .post('/auth/logout')
        .set('Authorization', `Bearer ${loginRes.body.accessToken}`);

      // Try to use refresh token after logout
      const refreshRes = await request(app)
        .post('/auth/refresh')
        .send({ refreshToken });

      expect(refreshRes.status).toBe(401);
    });
  });

  describe('Protected Routes', () => {
    let accessToken;

    beforeEach(async () => {
      const res = await request(app)
        .post('/auth/login')
        .send({
          email: 'test@example.com',
          password: 'ValidPassword123!'
        });

      accessToken = res.body.accessToken;
    });

    it('should access protected route with valid token', async () => {
      const res = await request(app)
        .get('/api/protected')
        .set('Authorization', `Bearer ${accessToken}`);

      expect(res.status).toBe(200);
    });

    it('should reject access without token', async () => {
      const res = await request(app)
        .get('/api/protected');

      expect(res.status).toBe(401);
    });

    it('should enforce role-based access control', async () => {
      // User without admin role
      const res = await request(app)
        .get('/api/admin/users')
        .set('Authorization', `Bearer ${accessToken}`);

      expect(res.status).toBe(403);
      expect(res.body.error).toMatch(/forbidden|permission/i);
    });
  });

  describe('Security', () => {
    it('should not leak password in responses', async () => {
      const res = await request(app)
        .post('/auth/login')
        .send({
          email: 'test@example.com',
          password: 'ValidPassword123!'
        });

      expect(res.body.user).not.toHaveProperty('password');
      expect(res.body.user).not.toHaveProperty('password_hash');
      expect(JSON.stringify(res.body)).not.toContain('password');
    });

    it('should not be vulnerable to XSS in error messages', async () => {
      const res = await request(app)
        .post('/auth/login')
        .send({
          email: '<script>alert(1)</script>@example.com',
          password: 'test'
        });

      expect(res.body.error).not.toContain('<script>');
      expect(res.body.error).not.toContain('</script>');
    });

    it('should have CSRF protection enabled', async () => {
      // This test depends on your CSRF implementation
      const res = await request(app)
        .post('/auth/login')
        .send({
          email: 'test@example.com',
          password: 'ValidPassword123!'
        });
      // Add CSRF token validation test here
    });
  });

  describe('Performance', () => {
    it('should handle concurrent logins', async () => {
      const promises = Array(100).fill(null).map(() =>
        request(app)
          .post('/auth/login')
          .send({
            email: 'test@example.com',
            password: 'ValidPassword123!'
          })
      );

      const results = await Promise.all(promises);

      const successCount = results.filter(r => r.status === 200).length;
      expect(successCount).toBe(100);
    });

    it('should validate tokens quickly', async () => {
      const loginRes = await request(app)
        .post('/auth/login')
        .send({
          email: 'test@example.com',
          password: 'ValidPassword123!'
        });

      const { accessToken } = loginRes.body;

      const start = Date.now();

      await request(app)
        .get('/api/protected')
        .set('Authorization', `Bearer ${accessToken}`);

      const duration = Date.now() - start;
      expect(duration).toBeLessThan(50); // Should be very fast
    });
  });
});
```

## Run Auth Tests

```bash
# Run all auth tests
npm test auth

# Run specific test suite
npm test auth.test.js

# Run with coverage
npm test auth -- --coverage

# Watch mode (development)
npm test auth -- --watch

# Verbose output
npm test auth -- --verbose
```

## Test Coverage Report

```
PASS tests/auth.test.js
  Authentication System
    POST /auth/login
      ✓ should login with valid credentials (234ms)
      ✓ should fail with invalid email (45ms)
      ✓ should fail with invalid password (89ms)
      ✓ should fail with missing fields (12ms)
      ✓ should rate limit failed login attempts (456ms)
      ✓ should not be vulnerable to SQL injection (34ms)
      ✓ should complete within 500ms (123ms)
    Token Validation
      ✓ should validate correct token structure (5ms)
      ✓ should reject expired token (23ms)
      ✓ should reject tampered token (18ms)
      ✓ should reject token with wrong algorithm (15ms)
    POST /auth/refresh
      ✓ should generate new access token (67ms)
      ✓ should invalidate old refresh token (89ms)
      ✓ should reject invalid refresh token (12ms)
    POST /auth/logout
      ✓ should logout successfully (45ms)
      ✓ should invalidate refresh token (78ms)
    Protected Routes
      ✓ should access protected route with valid token (34ms)
      ✓ should reject access without token (12ms)
      ✓ should enforce role-based access control (45ms)
    Security
      ✓ should not leak password in responses (56ms)
      ✓ should not be vulnerable to XSS (23ms)
      ✓ should have CSRF protection enabled (34ms)
    Performance
      ✓ should handle concurrent logins (1234ms)
      ✓ should validate tokens quickly (8ms)

Test Suites: 1 passed, 1 total
Tests:       23 passed, 23 total
Snapshots:   0 total
Time:        3.456s

Coverage:
  File              | % Stmts | % Branch | % Funcs | % Lines |
  ------------------|---------|----------|---------|---------|
  auth/             |   98.5  |   95.2   |  100.0  |   98.5  |
    jwt.js          |  100.0  |  100.0   |  100.0  |  100.0  |
    middleware.js   |   97.8  |   91.7   |  100.0  |   97.8  |
    routes.js       |   98.2  |   94.4   |  100.0  |   98.2  |
  ------------------|---------|----------|---------|---------|
```

## CI/CD Integration

```yaml
# .github/workflows/auth-tests.yml
name: Auth Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    paths:
      - 'src/auth/**'
      - 'tests/auth/**'

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install dependencies
        run: npm ci

      - name: Run auth tests
        run: npm test auth -- --coverage

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage/lcov.info

      - name: Check coverage threshold
        run: |
          COVERAGE=$(cat coverage/coverage-summary.json | jq '.total.lines.pct')
          if (( $(echo "$COVERAGE < 90" | bc -l) )); then
            echo "Coverage is below 90%: $COVERAGE%"
            exit 1
          fi
```

## Best Practices

**DO**:

- ✓ Test all authentication endpoints
- ✓ Test security vulnerabilities (SQL injection, XSS, CSRF)
- ✓ Test edge cases (expired tokens, invalid tokens, etc.)
- ✓ Test performance under load
- ✓ Achieve > 90% test coverage for auth code
- ✓ Run tests in CI/CD pipeline
- ✓ Test RBAC and permissions

**DON'T**:

- ✗ Skip security tests
- ✗ Use real credentials in tests
- ✗ Test only happy paths
- ✗ Ignore performance testing
- ✗ Commit test credentials to version control

## Commands

**`/auth/test`** - Run all auth tests
**`/auth/test --endpoint login`** - Test specific endpoint
**`/auth/test --coverage`** - Run with coverage report
**`/auth/setup jwt`** - Setup auth (auto-generates tests)
**`/dev/test`** - Run all tests (includes auth)

## Success Criteria

- ✓ All auth endpoints tested
- ✓ Security vulnerabilities tested (SQL injection, XSS, CSRF)
- ✓ Token validation tests pass
- ✓ RBAC tests pass
- ✓ Performance tests pass (< 500ms login, < 50ms validation)
- ✓ Test coverage > 90%
- ✓ No sensitive data leaked in responses
- ✓ Tests run in CI/CD pipeline

---
**Uses**: gcp-security-compliance, healthcare-security-compliance, qa-testing-engineer
