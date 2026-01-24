---
description: Generate integration tests for APIs/services with AI assistance
argument-hint: [api-endpoint or service-name]
model: claude-sonnet-4-5-20250929
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, AskUserQuestion
---

Generate integration tests for: **${ARGUMENTS}**

## What This Command Does

This command generates comprehensive integration tests that validate how multiple components, services, and APIs work together. Unlike unit tests that test isolated functions, integration tests verify real interactions between systems including databases, APIs, message queues, and external services.

**Key Capabilities**:

- Generates API endpoint tests with real HTTP requests
- Creates database integration tests with real queries
- Tests service-to-service communication
- Validates authentication/authorization flows
- Tests external API integrations
- Includes setup/teardown for test data and environments

## Step 1: Identify Integration Target

Parse arguments to determine what to test:

```bash
# Detect target type
case "$ARGUMENTS" in
  *"/api/"*|*"/v1/"*|*"/graphql"*)
    TEST_TYPE="api"
    echo "Detected API endpoint: $ARGUMENTS"
    ;;
  *"Service"*|*"service"*)
    TEST_TYPE="service"
    echo "Detected service: $ARGUMENTS"
    ;;
  *"Controller"*|*"controller"*)
    TEST_TYPE="controller"
    echo "Detected controller: $ARGUMENTS"
    ;;
  *)
    # Ask user
    echo "What type of integration test?"
    echo "1) REST API endpoint"
    echo "2) GraphQL API"
    echo "3) Service integration"
    echo "4) Database operations"
    echo "5) Message queue (Kafka, RabbitMQ)"
    ;;
esac
```

## Step 2: Analyze System Architecture

**Identify integration points**:

```bash
# Find API route definitions
grep -r "app.get\|app.post\|app.put\|app.delete" src/ --include="*.ts" --include="*.js"

# Find service dependencies
grep -r "constructor\|inject\|@Inject" src/ --include="*.ts"

# Find database models
find src/ -name "*model.ts" -o -name "*schema.ts"

# Find external API calls
grep -r "axios\|fetch\|http.request" src/ --include="*.ts" --include="*.js"
```

**Read relevant files**:

```javascript
// Read API routes
const routeFile = await Read({ file_path: 'src/routes/users.ts' })

// Read service implementation
const serviceFile = await Read({ file_path: 'src/services/userService.ts' })

// Read database models
const modelFile = await Read({ file_path: 'src/models/user.ts' })
```

## Step 3: Determine Test Framework and Tools

**Detect integration test tools**:

```bash
# Check package.json for tools
cat package.json | grep -E "supertest|newman|postman|rest-assured|pytest-integration"

# Common setups:
# - JavaScript/TypeScript: supertest + jest/vitest
# - Python: pytest + requests
# - Java: rest-assured + junit
# - Go: httptest + testify
```

**Identify database**:

```bash
# Detect database type
if grep -q "pg\|postgres" package.json; then
  DATABASE="postgresql"
elif grep -q "mysql" package.json; then
  DATABASE="mysql"
elif grep -q "mongodb" package.json; then
  DATABASE="mongodb"
fi

echo "Detected database: $DATABASE"
```

## Step 4: Set Up Test Environment

**Create test configuration**:

```typescript
// tests/integration/setup.ts
import { startServer } from './testServer'
import { initDatabase } from './testDatabase'

export async function setupTestEnvironment() {
  // 1. Start test database
  const db = await initDatabase({
    database: 'test_db',
    dropBeforeRun: true
  })

  // 2. Run migrations
  await db.runMigrations()

  // 3. Start server on test port
  const server = await startServer({
    port: 3001,
    database: db,
    env: 'test'
  })

  return { server, db }
}

export async function teardownTestEnvironment(env) {
  // 1. Stop server
  await env.server.close()

  // 2. Drop test database
  await env.db.dropDatabase()

  // 3. Close connections
  await env.db.close()
}
```

## Step 5: Generate API Integration Tests

### 5a. REST API Tests

**Generate endpoint tests**:

```typescript
import request from 'supertest'
import { app } from '../src/app'
import { setupTestEnvironment, teardownTestEnvironment } from './setup'

describe('User API Integration Tests', () => {
  let testEnv

  beforeAll(async () => {
    testEnv = await setupTestEnvironment()
  })

  afterAll(async () => {
    await teardownTestEnvironment(testEnv)
  })

  describe('POST /api/users', () => {
    it('should create new user with valid data', async () => {
      const userData = {
        email: 'test@example.com',
        name: 'Test User',
        password: 'SecurePass123!'
      }

      const response = await request(app)
        .post('/api/users')
        .send(userData)
        .expect(201)

      expect(response.body).toMatchObject({
        id: expect.any(Number),
        email: userData.email,
        name: userData.name,
        createdAt: expect.any(String)
      })
      expect(response.body.password).toBeUndefined() // Should not return password
    })

    it('should return 400 for invalid email', async () => {
      const response = await request(app)
        .post('/api/users')
        .send({
          email: 'invalid-email',
          name: 'Test User',
          password: 'SecurePass123!'
        })
        .expect(400)

      expect(response.body.error).toContain('Invalid email')
    })

    it('should return 409 for duplicate email', async () => {
      const userData = {
        email: 'duplicate@example.com',
        name: 'Test User',
        password: 'SecurePass123!'
      }

      // Create first user
      await request(app).post('/api/users').send(userData).expect(201)

      // Try to create duplicate
      const response = await request(app)
        .post('/api/users')
        .send(userData)
        .expect(409)

      expect(response.body.error).toContain('already exists')
    })
  })

  describe('GET /api/users/:id', () => {
    let userId

    beforeEach(async () => {
      // Create user for each test
      const response = await request(app)
        .post('/api/users')
        .send({
          email: 'gettest@example.com',
          name: 'Get Test User',
          password: 'SecurePass123!'
        })
      userId = response.body.id
    })

    it('should retrieve user by id', async () => {
      const response = await request(app)
        .get(`/api/users/${userId}`)
        .expect(200)

      expect(response.body).toMatchObject({
        id: userId,
        email: 'gettest@example.com',
        name: 'Get Test User'
      })
    })

    it('should return 404 for non-existent user', async () => {
      const response = await request(app)
        .get('/api/users/99999')
        .expect(404)

      expect(response.body.error).toContain('not found')
    })
  })

  describe('Authentication Flow', () => {
    let authToken

    it('should authenticate user and return token', async () => {
      // 1. Create user
      await request(app)
        .post('/api/users')
        .send({
          email: 'auth@example.com',
          name: 'Auth User',
          password: 'SecurePass123!'
        })

      // 2. Login
      const loginResponse = await request(app)
        .post('/api/auth/login')
        .send({
          email: 'auth@example.com',
          password: 'SecurePass123!'
        })
        .expect(200)

      expect(loginResponse.body).toHaveProperty('token')
      authToken = loginResponse.body.token
    })

    it('should access protected route with valid token', async () => {
      const response = await request(app)
        .get('/api/users/me')
        .set('Authorization', `Bearer ${authToken}`)
        .expect(200)

      expect(response.body.email).toBe('auth@example.com')
    })

    it('should reject protected route without token', async () => {
      await request(app)
        .get('/api/users/me')
        .expect(401)
    })

    it('should reject protected route with invalid token', async () => {
      await request(app)
        .get('/api/users/me')
        .set('Authorization', 'Bearer invalid-token')
        .expect(401)
    })
  })
})
```

### 5b. GraphQL API Tests

**Generate GraphQL tests**:

```typescript
import { graphqlRequest } from './graphqlTestUtils'

describe('GraphQL API Integration Tests', () => {
  describe('Queries', () => {
    it('should query user by id', async () => {
      const query = `
        query GetUser($id: ID!) {
          user(id: $id) {
            id
            email
            name
            posts {
              id
              title
            }
          }
        }
      `

      const response = await graphqlRequest(query, { id: '1' })

      expect(response.data.user).toBeDefined()
      expect(response.data.user.posts).toBeInstanceOf(Array)
    })
  })

  describe('Mutations', () => {
    it('should create user via mutation', async () => {
      const mutation = `
        mutation CreateUser($input: CreateUserInput!) {
          createUser(input: $input) {
            id
            email
            name
          }
        }
      `

      const variables = {
        input: {
          email: 'graphql@example.com',
          name: 'GraphQL User',
          password: 'SecurePass123!'
        }
      }

      const response = await graphqlRequest(mutation, variables)

      expect(response.data.createUser).toMatchObject({
        email: 'graphql@example.com',
        name: 'GraphQL User'
      })
    })
  })
})
```

## Step 6: Generate Database Integration Tests

**Test database operations**:

```typescript
describe('Database Integration Tests', () => {
  let db

  beforeAll(async () => {
    db = await connectToTestDatabase()
  })

  afterAll(async () => {
    await db.close()
  })

  afterEach(async () => {
    // Clean up after each test
    await db.query('DELETE FROM users')
  })

  describe('User Repository', () => {
    it('should create user and persist to database', async () => {
      const user = await userRepository.create({
        email: 'db@example.com',
        name: 'DB User'
      })

      // Verify in database
      const result = await db.query(
        'SELECT * FROM users WHERE id = $1',
        [user.id]
      )

      expect(result.rows[0]).toMatchObject({
        id: user.id,
        email: 'db@example.com',
        name: 'DB User'
      })
    })

    it('should enforce unique email constraint', async () => {
      await userRepository.create({
        email: 'unique@example.com',
        name: 'User 1'
      })

      await expect(
        userRepository.create({
          email: 'unique@example.com',
          name: 'User 2'
        })
      ).rejects.toThrow('duplicate key')
    })

    it('should handle transactions correctly', async () => {
      await db.transaction(async (trx) => {
        await trx.query('INSERT INTO users (email) VALUES ($1)', ['tx@example.com'])
        await trx.query('INSERT INTO profiles (user_email) VALUES ($1)', ['tx@example.com'])
        // Transaction commits
      })

      // Verify both inserts succeeded
      const users = await db.query('SELECT * FROM users WHERE email = $1', ['tx@example.com'])
      const profiles = await db.query('SELECT * FROM profiles WHERE user_email = $1', ['tx@example.com'])

      expect(users.rows).toHaveLength(1)
      expect(profiles.rows).toHaveLength(1)
    })

    it('should rollback failed transactions', async () => {
      await expect(
        db.transaction(async (trx) => {
          await trx.query('INSERT INTO users (email) VALUES ($1)', ['rollback@example.com'])
          throw new Error('Force rollback')
        })
      ).rejects.toThrow('Force rollback')

      // Verify insert was rolled back
      const result = await db.query('SELECT * FROM users WHERE email = $1', ['rollback@example.com'])
      expect(result.rows).toHaveLength(0)
    })
  })
})
```

## Step 7: Generate Service Integration Tests

**Test service interactions**:

```typescript
describe('Service Integration Tests', () => {
  let userService
  let emailService
  let paymentService

  beforeEach(() => {
    userService = new UserService()
    emailService = new EmailService()
    paymentService = new PaymentService()
  })

  describe('User Registration Flow', () => {
    it('should complete full registration with email and payment', async () => {
      // 1. Create user
      const user = await userService.register({
        email: 'integration@example.com',
        name: 'Integration Test',
        password: 'SecurePass123!'
      })

      expect(user.id).toBeDefined()
      expect(user.email).toBe('integration@example.com')

      // 2. Verify welcome email sent
      const emails = await emailService.getSentEmails()
      expect(emails).toContainEqual(
        expect.objectContaining({
          to: 'integration@example.com',
          subject: expect.stringContaining('Welcome')
        })
      )

      // 3. Process initial payment
      const payment = await paymentService.processPayment({
        userId: user.id,
        amount: 29.99,
        currency: 'USD'
      })

      expect(payment.status).toBe('completed')

      // 4. Verify user subscription activated
      const updatedUser = await userService.getById(user.id)
      expect(updatedUser.subscriptionStatus).toBe('active')
    })
  })

  describe('Error Handling Across Services', () => {
    it('should handle payment failure and notify user', async () => {
      const user = await userService.register({
        email: 'payment-fail@example.com',
        name: 'Payment Fail Test',
        password: 'SecurePass123!'
      })

      // Mock payment failure
      paymentService.mockFailure('insufficient_funds')

      await expect(
        paymentService.processPayment({
          userId: user.id,
          amount: 29.99
        })
      ).rejects.toThrow('insufficient_funds')

      // Verify failure email sent
      const emails = await emailService.getSentEmails()
      expect(emails).toContainEqual(
        expect.objectContaining({
          to: 'payment-fail@example.com',
          subject: expect.stringContaining('Payment Failed')
        })
      )

      // Verify user subscription not activated
      const updatedUser = await userService.getById(user.id)
      expect(updatedUser.subscriptionStatus).toBe('pending')
    })
  })
})
```

## Step 8: Run Integration Tests

**Execute test suite**:

```bash
# Run all integration tests
npm run test:integration

# Run with coverage
npm run test:integration -- --coverage

# Run specific test file
npm run test:integration -- users.integration.test.ts

# Run in watch mode
npm run test:integration -- --watch

# Run with verbose output
npm run test:integration -- --verbose
```

## Step 9: Generate Test Report

```
═══════════════════════════════════════════════════
         INTEGRATION TEST GENERATION REPORT
═══════════════════════════════════════════════════

TARGET: User API & Service Layer

TEST FILES CREATED:
  tests/integration/api/users.integration.test.ts
  tests/integration/services/userService.integration.test.ts
  tests/integration/database/userRepository.integration.test.ts

TEST SUITE SUMMARY:
  ✓ 28 integration test cases generated
  ✓ 6 API endpoint flows tested
  ✓ 4 database operations validated
  ✓ 3 service integrations tested
  ✓ Full authentication flow covered

TEST BREAKDOWN:

  1. API Endpoints (12 tests)
     ✓ POST /api/users (create user)
     ✓ GET /api/users/:id (retrieve user)
     ✓ PUT /api/users/:id (update user)
     ✓ DELETE /api/users/:id (delete user)
     ✓ Authentication flow (4 tests)
     ✓ Authorization checks (3 tests)

  2. Database Operations (8 tests)
     ✓ Create/Read/Update/Delete operations
     ✓ Transaction handling (commit & rollback)
     ✓ Constraint validation
     ✓ Concurrent access handling

  3. Service Integration (8 tests)
     ✓ User registration flow (with email & payment)
     ✓ Error handling across services
     ✓ Event publishing and consumption
     ✓ Cache invalidation

DEPENDENCIES TESTED:
  ✓ PostgreSQL database
  ✓ Redis cache
  ✓ Email service (SendGrid)
  ✓ Payment service (Stripe)

TEST RESULTS:
  ✓ All 28 tests passing
  ⏱ Duration: 8.5s
  📊 API Coverage: 95%

SETUP/TEARDOWN:
  ✓ Test database initialization
  ✓ Data cleanup after each test
  ✓ Connection pool management
  ✓ Mock service configurations

═══════════════════════════════════════════════════

NEXT STEPS:

1. Review generated tests:
   code tests/integration/api/users.integration.test.ts

2. Run integration tests:
   npm run test:integration

3. Add to CI/CD pipeline:
   - Run on every PR
   - Use isolated test database
   - Configure test environment variables

4. Monitor test performance:
   - Keep tests under 30 seconds total
   - Optimize slow tests
   - Parallelize when possible

═══════════════════════════════════════════════════
```

## Usage Examples

**Generate API tests**:

```bash
/testing:integration /api/users
```

**Generate service tests**:

```bash
/testing:integration UserService
```

**Generate database tests**:

```bash
/testing:integration UserRepository
```

**Generate full flow tests**:

```bash
/testing:integration "user registration flow"
```

## Business Value / ROI

**Cost of Integration Bugs**:

- Production API bug: $10,000-$100,000
- Database corruption: $50,000-$500,000
- Payment processing failure: $100,000+
- **Integration tests prevent these failures**

**Time Savings**:

- Manual integration testing: 4-8 hours per feature
- AI-assisted generation: 15-30 minutes
- **ROI: 90%+ time reduction**

**Quality Improvements**:

- Catches integration issues before production
- Validates entire user flows
- Tests real database interactions
- **Reduces production incidents by 70-85%**

**Confidence in Deployments**:

- Verify API contracts maintained
- Validate database migrations
- Ensure backward compatibility
- **Enables continuous deployment**

## Success Metrics

**Test Coverage**:

- [ ] All API endpoints tested (CRUD operations)
- [ ] Authentication/authorization flows validated
- [ ] Database operations tested with real database
- [ ] Service interactions verified
- [ ] Error scenarios covered

**Test Quality**:

- [ ] Tests use real dependencies (not mocked)
- [ ] Setup/teardown properly configured
- [ ] Tests are isolated (no side effects)
- [ ] Tests are idempotent (can run multiple times)
- [ ] Clear test names describe scenarios

**Performance**:

- [ ] Full suite completes in < 2 minutes
- [ ] Individual tests run in < 5 seconds
- [ ] Database cleanup is efficient
- [ ] No resource leaks (connections, memory)

**Reliability**:

- [ ] No flaky tests (99%+ consistency)
- [ ] Tests pass in CI environment
- [ ] Tests work on all platforms
- [ ] Proper error messages when failing

## Integration with Development Workflow

**During Development**:

- `/dev:implement` → `/testing:unit` → **`/testing:integration`** → `/dev:test`

**Before Deployment**:

- Run integration tests against staging environment
- Validate database migrations
- Test API backward compatibility

**CI/CD Pipeline**:

- Run on every pull request
- Block merge if integration tests fail
- Monitor test execution time trends

---

**Model**: Sonnet (complex integration test generation)
**Estimated time**: 15-30 minutes per service
**Tip**: Run integration tests in isolated environment with test database!
