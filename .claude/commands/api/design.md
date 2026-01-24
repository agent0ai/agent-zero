---
description: Design RESTful/GraphQL APIs with best practices
argument-hint: [--type rest|graphql] [--domain <domain>] [--preview]
model: claude-sonnet-4-5-20250929
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---

Design RESTful or GraphQL API with industry best practices: **$ARGUMENTS**

## What This Command Does

This command guides you through designing production-ready APIs following industry standards:

- **RESTful APIs**: Resource-based design with proper HTTP methods, status codes, and HATEOAS
- **GraphQL APIs**: Schema-first design with queries, mutations, subscriptions, and type system
- **Best Practices**: Authentication, versioning, pagination, error handling, rate limiting
- **Documentation**: Auto-generate OpenAPI/GraphQL schema documentation
- **Security**: OWASP API Security Top 10 compliance
- **Performance**: Caching strategies, N+1 query prevention, pagination patterns

## Usage Examples

### Basic REST API Design

```bash
/api:design --type rest --domain users
```

### GraphQL API Design

```bash
/api:design --type graphql --domain ecommerce
```

### Multi-Resource REST API

```bash
/api:design --type rest --domain "users,products,orders" --preview
```

### Design from Existing Database Schema

```bash
/api:design --type rest --from-database --schema ./schema.sql
```

## Step 1: Parse Arguments and Gather Context

```bash
# Parse arguments
TYPE="${TYPE:-rest}"  # rest or graphql
DOMAIN="$DOMAIN"      # Domain/resource name
PREVIEW="$PREVIEW"    # Preview only, don't write files

# Detect project type
if [ -f "package.json" ]; then
  LANG="nodejs"
elif [ -f "requirements.txt" ] || [ -f "setup.py" ]; then
  LANG="python"
elif [ -f "go.mod" ]; then
  LANG="go"
elif [ -f "pom.xml" ] || [ -f "build.gradle" ]; then
  LANG="java"
else
  LANG="unknown"
fi

echo "Designing $TYPE API for domain: $DOMAIN"
echo "Detected language: $LANG"
```

## Step 2: Interactive Requirements Gathering

Ask user about API requirements using structured questions:

**Question 1: API Purpose and Scope**

- What is the primary purpose of this API?
- Who are the consumers? (Web app, mobile app, third-party developers, internal services)
- What are the key resources/entities?
- What operations are needed? (CRUD, search, bulk operations, etc.)

**Question 2: Authentication & Authorization**

- What authentication method? (JWT, OAuth 2.0, API Keys, mTLS)
- What authorization model? (RBAC, ABAC, claims-based)
- Public endpoints vs. authenticated endpoints?
- Rate limiting requirements?

**Question 3: Data & Performance**

- Expected request volume? (requests/second)
- Data size per response? (pagination needed?)
- Real-time requirements? (webhooks, WebSockets, Server-Sent Events)
- Caching strategy? (CDN, Redis, HTTP caching)

**Question 4: Integration & Standards**

- Existing systems to integrate with?
- Industry standards to follow? (FHIR for healthcare, PSD2 for fintech)
- Compliance requirements? (GDPR, HIPAA, PCI-DSS)
- API versioning strategy?

## Step 3: Generate API Design

### For REST APIs

Generate comprehensive REST API design:

**Resource Identification**:

```
Identify primary resources:
- Users → /users
- Products → /products
- Orders → /orders

Identify sub-resources:
- User addresses → /users/{id}/addresses
- Product reviews → /products/{id}/reviews
- Order items → /orders/{id}/items
```

**HTTP Methods Mapping**:

```
GET    /users          → List all users (with pagination)
GET    /users/{id}     → Get specific user
POST   /users          → Create new user
PUT    /users/{id}     → Full update of user
PATCH  /users/{id}     → Partial update of user
DELETE /users/{id}     → Delete user

POST   /users/{id}/activate   → Activate user account
POST   /users/{id}/deactivate → Deactivate user account
```

**Status Codes**:

```
200 OK                  → Successful GET, PUT, PATCH
201 Created             → Successful POST with new resource
204 No Content          → Successful DELETE or action with no response body
400 Bad Request         → Invalid request format or validation errors
401 Unauthorized        → Missing or invalid authentication
403 Forbidden           → Authenticated but not authorized
404 Not Found           → Resource doesn't exist
409 Conflict            → Duplicate resource or business rule violation
422 Unprocessable Entity→ Validation errors with details
429 Too Many Requests   → Rate limit exceeded
500 Internal Server Error→ Server-side error
503 Service Unavailable → Maintenance or overload
```

**Request/Response Format**:

```json
// GET /users?page=1&limit=20&sort=created_at:desc
{
  "data": [
    {
      "id": "usr_123",
      "type": "user",
      "attributes": {
        "email": "john@example.com",
        "name": "John Doe",
        "created_at": "2024-01-15T10:30:00Z"
      },
      "relationships": {
        "orders": {
          "links": {
            "self": "/users/usr_123/relationships/orders",
            "related": "/users/usr_123/orders"
          }
        }
      },
      "links": {
        "self": "/users/usr_123"
      }
    }
  ],
  "meta": {
    "total": 1543,
    "page": 1,
    "per_page": 20,
    "total_pages": 78
  },
  "links": {
    "self": "/users?page=1&limit=20",
    "first": "/users?page=1&limit=20",
    "next": "/users?page=2&limit=20",
    "last": "/users?page=78&limit=20"
  }
}

// POST /users (Create)
{
  "data": {
    "type": "user",
    "attributes": {
      "email": "jane@example.com",
      "name": "Jane Smith",
      "password": "secure_password_here"
    }
  }
}

// Error Response (422)
{
  "errors": [
    {
      "id": "err_001",
      "status": "422",
      "code": "VALIDATION_ERROR",
      "title": "Validation Failed",
      "detail": "Email address is already in use",
      "source": {
        "pointer": "/data/attributes/email"
      }
    }
  ]
}
```

**Security Headers**:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
Accept: application/json
X-API-Version: v1
X-Request-ID: uuid-here

# Response headers
X-Rate-Limit-Limit: 1000
X-Rate-Limit-Remaining: 999
X-Rate-Limit-Reset: 1640000000
X-Request-ID: uuid-here
Cache-Control: max-age=3600, private
ETag: "33a64df551425fcc55e4d42a148795d9f25f89d4"
```

**Pagination Strategies**:

```
Offset-based:
GET /users?page=2&limit=20
GET /users?offset=20&limit=20

Cursor-based (recommended for large datasets):
GET /users?cursor=eyJpZCI6MTIzfQ&limit=20

Response includes next cursor:
{
  "data": [...],
  "pagination": {
    "next_cursor": "eyJpZCI6MTQzfQ",
    "has_more": true
  }
}
```

### For GraphQL APIs

Generate comprehensive GraphQL schema:

**Schema Definition**:

```graphql
# User type
type User {
  id: ID!
  email: String!
  name: String!
  createdAt: DateTime!
  updatedAt: DateTime!

  # Relationships
  orders(
    first: Int = 10
    after: String
    filter: OrderFilter
  ): OrderConnection!

  addresses: [Address!]!
}

# Pagination connection
type OrderConnection {
  edges: [OrderEdge!]!
  pageInfo: PageInfo!
  totalCount: Int!
}

type OrderEdge {
  node: Order!
  cursor: String!
}

type PageInfo {
  hasNextPage: Boolean!
  hasPreviousPage: Boolean!
  startCursor: String
  endCursor: String
}

# Order type
type Order {
  id: ID!
  status: OrderStatus!
  total: Money!
  items: [OrderItem!]!
  createdAt: DateTime!
  user: User!
}

enum OrderStatus {
  PENDING
  PROCESSING
  SHIPPED
  DELIVERED
  CANCELLED
}

# Custom scalars
scalar DateTime
scalar Money
scalar Email

# Input types
input CreateUserInput {
  email: Email!
  name: String!
  password: String!
}

input UpdateUserInput {
  email: Email
  name: String
}

input OrderFilter {
  status: OrderStatus
  minTotal: Money
  maxTotal: Money
  dateFrom: DateTime
  dateTo: DateTime
}

# Queries
type Query {
  # Single resource
  user(id: ID!): User
  order(id: ID!): Order

  # Lists with pagination
  users(
    first: Int = 10
    after: String
    filter: UserFilter
  ): UserConnection!

  orders(
    first: Int = 10
    after: String
    filter: OrderFilter
  ): OrderConnection!

  # Search
  searchUsers(query: String!): [User!]!

  # Me (authenticated user)
  me: User
}

# Mutations
type Mutation {
  # User operations
  createUser(input: CreateUserInput!): CreateUserPayload!
  updateUser(id: ID!, input: UpdateUserInput!): UpdateUserPayload!
  deleteUser(id: ID!): DeleteUserPayload!

  # Order operations
  createOrder(input: CreateOrderInput!): CreateOrderPayload!
  cancelOrder(id: ID!): CancelOrderPayload!
}

# Mutation payloads
type CreateUserPayload {
  user: User
  errors: [Error!]!
}

type UpdateUserPayload {
  user: User
  errors: [Error!]!
}

type Error {
  field: String
  message: String!
  code: String!
}

# Subscriptions (real-time)
type Subscription {
  orderStatusChanged(userId: ID!): Order!
  newOrder: Order!
}
```

**Resolver Structure**:

```javascript
// Resolvers implementation guide
const resolvers = {
  Query: {
    user: async (parent, { id }, context) => {
      // Check authentication
      if (!context.user) {
        throw new AuthenticationError('Must be authenticated')
      }

      // Check authorization
      if (context.user.id !== id && !context.user.isAdmin) {
        throw new ForbiddenError('Cannot access other users')
      }

      return await userService.findById(id)
    },

    users: async (parent, { first, after, filter }, context) => {
      // Pagination with DataLoader to prevent N+1
      return await userService.findMany({
        first,
        after,
        filter
      })
    }
  },

  Mutation: {
    createUser: async (parent, { input }, context) => {
      // Validate input
      const errors = validateCreateUserInput(input)
      if (errors.length > 0) {
        return { user: null, errors }
      }

      try {
        const user = await userService.create(input)
        return { user, errors: [] }
      } catch (error) {
        return {
          user: null,
          errors: [{ message: error.message, code: 'CREATE_FAILED' }]
        }
      }
    }
  },

  User: {
    // Field resolver with DataLoader
    orders: async (user, args, context) => {
      return context.loaders.ordersByUserId.load(user.id)
    }
  },

  Subscription: {
    orderStatusChanged: {
      subscribe: (parent, { userId }, context) => {
        return context.pubsub.asyncIterator([`ORDER_STATUS_${userId}`])
      }
    }
  }
}
```

## Step 4: Security Best Practices

Generate security implementation checklist:

**Authentication**:

```yaml
JWT Implementation:
  - Use RS256 (RSA) instead of HS256 for public APIs
  - Short access token expiry (15 minutes)
  - Refresh token rotation
  - Token blacklisting for logout
  - Secure token storage (httpOnly cookies)

OAuth 2.0:
  - Authorization Code flow with PKCE (for SPAs)
  - Client Credentials flow (for server-to-server)
  - Scope-based access control
  - State parameter for CSRF protection

API Keys:
  - Generate cryptographically secure keys
  - Prefix keys for identification (e.g., "pk_live_...")
  - Hash keys before storage
  - Support key rotation
  - Rate limit by key
```

**Authorization**:

```yaml
RBAC (Role-Based):
  roles:
    - admin: Full access
    - manager: Read/write to resources
    - user: Read own resources only
    - guest: Public endpoints only

ABAC (Attribute-Based):
  policies:
    - user.department == resource.department
    - user.clearance_level >= resource.classification
    - time.hour >= 9 AND time.hour <= 17
```

**Input Validation**:

```javascript
// Example validation
const createUserSchema = {
  email: {
    type: 'string',
    format: 'email',
    maxLength: 255,
    required: true
  },
  name: {
    type: 'string',
    minLength: 2,
    maxLength: 100,
    pattern: '^[a-zA-Z\\s]+$',
    required: true
  },
  password: {
    type: 'string',
    minLength: 12,
    pattern: '^(?=.*[a-z])(?=.*[A-Z])(?=.*\\d)(?=.*[@$!%*?&])',
    required: true
  }
}
```

**Rate Limiting**:

```yaml
Strategies:
  - Fixed window: 1000 requests per hour
  - Sliding window: 1000 requests per rolling hour
  - Token bucket: Burst allowance with refill rate
  - Leaky bucket: Smooth rate enforcement

Implementation:
  - Redis for distributed rate limiting
  - Rate limit by: IP, user ID, API key
  - Different limits per endpoint tier
  - Return 429 with Retry-After header
```

**OWASP API Security Top 10**:

```
1. Broken Object Level Authorization (BOLA)
   → Validate user owns resource before access

2. Broken Authentication
   → Implement strong authentication mechanisms

3. Broken Object Property Level Authorization
   → Filter response fields based on permissions

4. Unrestricted Resource Consumption
   → Implement rate limiting and pagination

5. Broken Function Level Authorization
   → Check permissions at every endpoint

6. Unrestricted Access to Sensitive Business Flows
   → Protect workflows (e.g., password reset)

7. Server Side Request Forgery (SSRF)
   → Validate and sanitize URLs

8. Security Misconfiguration
   → Secure defaults, disable debug in production

9. Improper Inventory Management
   → Document all endpoints and versions

10. Unsafe Consumption of APIs
    → Validate external API responses
```

## Step 5: API Versioning Strategy

Define versioning approach:

**URL Versioning** (Recommended for REST):

```
https://api.example.com/v1/users
https://api.example.com/v2/users

Pros: Clear, easy to implement, supports multiple versions
Cons: URL pollution, harder to deprecate
```

**Header Versioning**:

```
GET /users
Accept: application/vnd.example.v1+json

Pros: Clean URLs, flexible content negotiation
Cons: Less visible, requires client support
```

**GraphQL Versioning**:

```graphql
# Deprecate fields instead of versioning
type User {
  name: String! @deprecated(reason: "Use firstName and lastName")
  firstName: String!
  lastName: String!
}

# Evolution over versioning - add fields, don't remove
```

**Deprecation Process**:

```yaml
Phase 1 - Announce (3 months):
  - Add deprecation notice to docs
  - Return Deprecation header
  - Log usage of deprecated endpoints

Phase 2 - Warn (3 months):
  - Return Sunset header with date
  - Email developers using deprecated endpoints
  - Provide migration guide

Phase 3 - Deprecate (3 months):
  - Return 410 Gone for deprecated endpoints
  - Redirect to new endpoints if possible
  - Keep documentation available

Phase 4 - Remove:
  - Remove endpoint code
  - Archive documentation
```

## Step 6: Performance Optimization

Generate performance patterns:

**Caching Strategy**:

```yaml
HTTP Caching:
  Cache-Control: public, max-age=3600     # 1 hour
  Cache-Control: private, max-age=300     # 5 minutes (user-specific)
  Cache-Control: no-cache                 # Revalidate before use
  Cache-Control: no-store                 # Never cache

  ETag: "33a64df551425fcc55e4d42a148795d9f25f89d4"
  If-None-Match: "33a64df551425fcc55e4d42a148795d9f25f89d4"
  → Return 304 Not Modified if unchanged

Redis Caching:
  - Cache expensive queries (5-60 minutes)
  - Cache-aside pattern
  - Invalidate on writes
  - Use cache warming for predictable requests

CDN Caching:
  - Static assets: max-age=31536000 (1 year)
  - API responses: max-age=60-300 (1-5 minutes)
  - Geographic distribution
```

**N+1 Query Prevention**:

```javascript
// REST: Use include parameter
GET /orders?include=user,items

// GraphQL: DataLoader pattern
const userLoader = new DataLoader(async (userIds) => {
  const users = await db.users.findMany({
    where: { id: { in: userIds } }
  })
  return userIds.map(id => users.find(u => u.id === id))
})

// Batch database queries
const orders = await db.orders.findMany({ where: { userId: 123 } })
const userIds = orders.map(o => o.userId)
const users = await userLoader.loadMany(userIds)
```

**Pagination Best Practices**:

```yaml
Offset Pagination (Simple but inefficient):
  - Good for: Small datasets, random access needed
  - Bad for: Large datasets, frequent writes
  - Example: ?page=2&limit=20

Cursor Pagination (Recommended):
  - Good for: Large datasets, append-only data
  - Bad for: Random page access
  - Example: ?cursor=eyJpZCI6MTIzfQ&limit=20

Keyset Pagination (Best for ordered data):
  - Good for: Sorted data, stable ordering
  - Bad for: Complex sorting
  - Example: ?after_id=123&limit=20
```

**Compression**:

```yaml
Enable gzip/brotli compression:
  Accept-Encoding: gzip, br
  Content-Encoding: gzip

  Typical savings: 60-80% for JSON responses
```

## Step 7: Generate API Files

Create API specification files:

### REST API: OpenAPI Spec

```bash
# Generate OpenAPI 3.0 specification
cat > openapi.yaml <<'EOF'
openapi: 3.0.3
info:
  title: $DOMAIN API
  version: 1.0.0
  description: RESTful API for $DOMAIN management
  contact:
    email: api@example.com
  license:
    name: MIT

servers:
  - url: https://api.example.com/v1
    description: Production
  - url: https://staging-api.example.com/v1
    description: Staging

security:
  - bearerAuth: []

paths:
  /users:
    get:
      summary: List users
      parameters:
        - name: page
          in: query
          schema:
            type: integer
            default: 1
        - name: limit
          in: query
          schema:
            type: integer
            default: 20
            maximum: 100
      responses:
        '200':
          description: Successful response
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UserList'

    post:
      summary: Create user
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateUser'
      responses:
        '201':
          description: User created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'

components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT

  schemas:
    User:
      type: object
      properties:
        id:
          type: string
        email:
          type: string
          format: email
        name:
          type: string
        created_at:
          type: string
          format: date-time
EOF
```

### GraphQL: Schema File

```bash
cat > schema.graphql <<'EOF'
# Generated GraphQL Schema
# [Schema content from Step 3]
EOF
```

### API Documentation

```bash
mkdir -p docs/api
cat > docs/api/README.md <<'EOF'
# $DOMAIN API Documentation

## Overview
[Generated overview]

## Authentication
[Authentication guide]

## Rate Limiting
[Rate limit details]

## Examples
[Usage examples]
EOF
```

## Step 8: Implementation Stubs

Generate implementation stubs based on language:

### Node.js/Express

```javascript
// routes/users.js
const express = require('express')
const router = express.Router()
const { authenticate, authorize } = require('../middleware/auth')
const { validateRequest } = require('../middleware/validation')
const userController = require('../controllers/userController')

router.get('/users',
  authenticate,
  authorize(['admin', 'manager']),
  userController.list
)

router.post('/users',
  authenticate,
  validateRequest(createUserSchema),
  userController.create
)

module.exports = router
```

### Python/FastAPI

```python
# routers/users.py
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from models import User, CreateUser
from dependencies import get_current_user, check_permissions

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/", response_model=List[User])
async def list_users(
    page: int = 1,
    limit: int = 20,
    current_user: User = Depends(get_current_user)
):
    # Implementation
    pass

@router.post("/", response_model=User, status_code=201)
async def create_user(
    user: CreateUser,
    current_user: User = Depends(get_current_user)
):
    # Implementation
    pass
```

## Step 9: Testing Strategy

Generate test plan:

**Unit Tests**:

```javascript
describe('User API', () => {
  describe('POST /users', () => {
    it('should create user with valid data', async () => {
      const response = await request(app)
        .post('/users')
        .send({ email: 'test@example.com', name: 'Test' })
        .expect(201)

      expect(response.body.data.attributes.email).toBe('test@example.com')
    })

    it('should reject invalid email', async () => {
      const response = await request(app)
        .post('/users')
        .send({ email: 'invalid', name: 'Test' })
        .expect(422)

      expect(response.body.errors[0].code).toBe('VALIDATION_ERROR')
    })

    it('should require authentication', async () => {
      await request(app)
        .post('/users')
        .send({ email: 'test@example.com', name: 'Test' })
        .expect(401)
    })
  })
})
```

**Integration Tests**:

```javascript
describe('User Flow', () => {
  it('should complete full user lifecycle', async () => {
    // Create
    const createRes = await api.post('/users', userData)
    const userId = createRes.body.data.id

    // Read
    const getRes = await api.get(`/users/${userId}`)
    expect(getRes.body.data.id).toBe(userId)

    // Update
    await api.patch(`/users/${userId}`, { name: 'Updated' })

    // Delete
    await api.delete(`/users/${userId}`).expect(204)

    // Verify deleted
    await api.get(`/users/${userId}`).expect(404)
  })
})
```

**Contract Tests**:

```javascript
// Validate OpenAPI compliance
const validator = require('express-openapi-validator')

app.use(validator.middleware({
  apiSpec: './openapi.yaml',
  validateRequests: true,
  validateResponses: true
}))
```

## Step 10: Display Summary and Next Steps

```
════════════════════════════════════════════════════════
          API DESIGN COMPLETED
════════════════════════════════════════════════════════

API TYPE: REST
DOMAIN: users, products, orders
LANGUAGE: Node.js

FILES GENERATED:
✓ openapi.yaml - OpenAPI 3.0 specification
✓ docs/api/README.md - API documentation
✓ routes/users.js - User endpoints
✓ routes/products.js - Product endpoints
✓ routes/orders.js - Order endpoints
✓ middleware/auth.js - Authentication middleware
✓ middleware/validation.js - Request validation
✓ tests/api/users.test.js - User API tests

ENDPOINTS DESIGNED:
  GET    /v1/users               List users
  GET    /v1/users/:id           Get user
  POST   /v1/users               Create user
  PATCH  /v1/users/:id           Update user
  DELETE /v1/users/:id           Delete user

  [12 more endpoints...]

SECURITY:
✓ JWT authentication
✓ Role-based authorization (admin, manager, user)
✓ Rate limiting (1000 req/hour)
✓ Input validation
✓ OWASP API Security compliance

PERFORMANCE:
✓ Cursor-based pagination
✓ HTTP caching (ETags)
✓ Redis caching strategy
✓ Gzip compression

════════════════════════════════════════════════════════

NEXT STEPS:

1. Review generated OpenAPI spec:
   npx @redocly/cli preview-docs openapi.yaml

2. Generate API documentation:
   /api:document

3. Implement endpoints:
   - Install dependencies: npm install
   - Run tests: npm test
   - Start dev server: npm run dev

4. Generate API mocks for testing:
   /api:mock --from openapi.yaml

5. Set up versioning strategy:
   /api:version --strategy url --initial v1

════════════════════════════════════════════════════════

DOCUMENTATION:
📖 API Docs: http://localhost:8080/docs
📖 OpenAPI Spec: ./openapi.yaml
📖 Postman Collection: ./postman_collection.json

════════════════════════════════════════════════════════
```

## Business Value & ROI

**Time Savings**:

- Manual API design: 2-5 days
- With this command: 15-30 minutes
- **ROI: 10-20x faster**

**Quality Improvements**:

- ✓ Best practices enforced automatically
- ✓ Security vulnerabilities prevented
- ✓ Performance patterns built-in
- ✓ Complete documentation from day one

**Cost Savings**:

- Prevent costly refactoring from poor initial design
- Reduce API-related bugs by 60-80%
- Decrease onboarding time for new developers
- Minimize security incidents

**Business Impact**:

- Faster time-to-market for API features
- Better developer experience (internal & external)
- Easier API governance and compliance
- Scalable architecture from the start

## Success Metrics

Track these KPIs after implementation:

**Development Metrics**:

- API design time: Target < 1 hour
- Time to first working endpoint: Target < 30 minutes
- Test coverage: Target > 80%
- Documentation completeness: Target 100%

**API Performance**:

- Response time P95: Target < 200ms
- Error rate: Target < 0.1%
- Rate limit violations: Monitor
- Cache hit ratio: Target > 70%

**Developer Experience**:

- Time to integrate: Target < 2 hours
- API calls requiring support: Target < 5%
- Developer satisfaction score: Target > 4.5/5
- Breaking changes per version: Target < 1

**Security**:

- Security audit score: Target > 90%
- OWASP API Top 10 compliance: 100%
- Authentication failures: Monitor for attacks
- Authorization bypass attempts: Zero tolerance

---

**Model**: Claude Sonnet 4.5 (complex architecture and reasoning)
**Estimated time**: 15-30 minutes for complete API design
**Requirements**: Language-specific runtime (Node.js, Python, etc.)
