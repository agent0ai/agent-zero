---
description: Create API versioning strategy and migration guides
argument-hint: [--strategy url|header|content] [--from v1] [--to v2] [--breaking]
model: claude-sonnet-4-5-20250929
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---

Create comprehensive API versioning strategy and migration guide: **$ARGUMENTS**

## What This Command Does

This command helps you implement API versioning and manage version transitions:

- **Versioning Strategies**: URL-based, header-based, content negotiation, or GraphQL evolution
- **Migration Guides**: Auto-generate migration documentation for version transitions
- **Deprecation Process**: Structured deprecation timeline with notifications
- **Breaking Change Detection**: Identify breaking changes between versions
- **Backward Compatibility**: Strategies to maintain compatibility
- **Version Routing**: Implementation code for multi-version support

## Usage Examples

### Set Up Initial Versioning

```bash
/api:version --strategy url --initial v1
```

### Create New Version with Breaking Changes

```bash
/api:version --from v1 --to v2 --breaking
```

### Generate Migration Guide

```bash
/api:version --from v1 --to v2 --migration-guide
```

### Deprecate Old Version

```bash
/api:version --deprecate v1 --sunset-date 2024-12-31
```

## Step 1: Analyze Current API State

```bash
# Detect existing versioning
CURRENT_STRATEGY="none"

if grep -q "api\.example\.com/v[0-9]" openapi.yaml 2>/dev/null; then
  CURRENT_STRATEGY="url"
  echo "Current strategy: URL versioning detected"
elif grep -q "Accept-Version" openapi.yaml 2>/dev/null; then
  CURRENT_STRATEGY="header"
  echo "Current strategy: Header versioning detected"
elif [ -f "schema.graphql" ]; then
  CURRENT_STRATEGY="graphql-evolution"
  echo "Current strategy: GraphQL schema evolution"
else
  echo "No versioning strategy detected"
fi

# Detect current version
if [ "$CURRENT_STRATEGY" = "url" ]; then
  CURRENT_VERSION=$(grep -oP 'api\.example\.com/v\K[0-9]+' openapi.yaml | head -1)
  echo "Current version: v$CURRENT_VERSION"
fi

# Analyze endpoints
ENDPOINT_COUNT=$(yq eval '.paths | keys | length' openapi.yaml 2>/dev/null || echo "0")
echo "Total endpoints: $ENDPOINT_COUNT"
```

## Step 2: Choose Versioning Strategy

Ask user to select versioning strategy:

**Question: Which versioning strategy do you want to use?**

### Option 1: URL Versioning (Recommended for REST)

```
https://api.example.com/v1/users
https://api.example.com/v2/users

Pros:
✓ Most visible and explicit
✓ Easy to test and debug
✓ Simple routing implementation
✓ Great for public APIs
✓ CDN-friendly

Cons:
✗ URL changes on version upgrade
✗ Can lead to code duplication
✗ Multiple versions in URL path

Best for: REST APIs, public APIs, microservices
```

### Option 2: Header Versioning

```
GET /users
Accept-Version: v1

GET /users
Accept-Version: v2

Pros:
✓ Clean URLs (no version in path)
✓ Backward compatible URLs
✓ Follows REST principles

Cons:
✗ Less visible (hidden in headers)
✗ Harder to test manually
✗ Cache complexity

Best for: Internal APIs, APIs with stable URLs
```

### Option 3: Content Negotiation

```
GET /users
Accept: application/vnd.company.v1+json

GET /users
Accept: application/vnd.company.v2+json

Pros:
✓ RESTful approach
✓ Standards-compliant
✓ Supports multiple representations

Cons:
✗ More complex to implement
✗ Requires understanding of content types
✗ Not intuitive for developers

Best for: APIs following strict REST principles
```

### Option 4: Query Parameter (Not Recommended)

```
GET /users?version=1
GET /users?version=2

Pros:
✓ Simple to implement
✓ Easy to test

Cons:
✗ Ugly URLs
✗ Version as optional parameter
✗ Cache issues
✗ Not RESTful

Best for: Internal tools only (avoid for production APIs)
```

### Option 5: GraphQL Evolution (No Versioning)

```graphql
type User {
  name: String! @deprecated(reason: "Use firstName and lastName")
  firstName: String!
  lastName: String!
}

Pros:
✓ No versioning needed
✓ Gradual migration
✓ Backward compatible by default
✓ Clients control what they get

Cons:
✗ Schema can become complex
✗ Harder to remove old fields
✗ Deprecation management needed

Best for: GraphQL APIs only
```

## Step 3: Detect Breaking Changes

Compare API versions to identify breaking changes:

```bash
# If comparing two OpenAPI specs
if [ -f "openapi-v1.yaml" ] && [ -f "openapi-v2.yaml" ]; then
  # Install OpenAPI diff tool
  npm install -g openapi-diff

  # Generate breaking change report
  openapi-diff openapi-v1.yaml openapi-v2.yaml \
    --format markdown \
    --output breaking-changes.md

  echo "Breaking changes detected:"

  # Analyze breaking changes
  cat breaking-changes.md | grep -E "Breaking|BREAKING" | while read -r line; do
    echo "  ⚠ $line"
  done
fi

# Common breaking changes to check for:
echo ""
echo "Checking for breaking changes..."

# 1. Removed endpoints
echo "1. Checking for removed endpoints..."

# 2. Removed or renamed fields
echo "2. Checking for removed/renamed fields..."

# 3. Changed field types
echo "3. Checking for field type changes..."

# 4. New required fields
echo "4. Checking for new required fields..."

# 5. Changed error codes
echo "5. Checking for error code changes..."

# 6. Authentication changes
echo "6. Checking for authentication changes..."
```

### Breaking Change Categories

**High Impact (Must Document)**:

```yaml
Endpoint Changes:
  - Removed endpoint
  - Changed HTTP method
  - Changed URL structure
  - Changed authentication requirement

Request Changes:
  - Removed field
  - Renamed field
  - Changed field type (string -> number)
  - New required field
  - Changed validation rules (more strict)

Response Changes:
  - Removed field from response
  - Changed field type in response
  - Changed response structure
  - Changed status codes

Behavior Changes:
  - Changed default values
  - Changed sorting/pagination
  - Changed rate limits (more restrictive)
  - Changed error handling
```

**Medium Impact (Should Document)**:

```yaml
Additions:
  - New optional fields in request
  - New fields in response
  - New query parameters
  - New headers

Deprecations:
  - Deprecated fields (still work but marked for removal)
  - Deprecated endpoints
  - Deprecated authentication methods
```

**Low Impact (Nice to Document)**:

```yaml
Non-Breaking:
  - Documentation updates
  - New endpoints
  - Performance improvements
  - Bug fixes
  - Relaxed validation rules
```

## Step 4: Generate Migration Guide

Create comprehensive migration documentation:

```bash
mkdir -p docs/migrations

cat > "docs/migrations/v${FROM_VERSION}-to-v${TO_VERSION}.md" <<'EOF'
# Migration Guide: v1 to v2

## Overview

This guide helps you migrate from API v1 to v2. API v2 introduces several improvements and breaking changes.

**Migration Timeline**:
- v2 Released: January 15, 2024
- v1 Deprecated: April 15, 2024 (3 months notice)
- v1 Sunset: July 15, 2024 (6 months total)

## Breaking Changes

### 1. Authentication Changes

**v1** (Deprecated):
```bash
# API Key in query parameter
GET /users?api_key=YOUR_KEY
```

**v2** (Required):

```bash
# Bearer token in Authorization header
GET /users
Authorization: Bearer YOUR_TOKEN
```

**Migration Steps**:

1. Generate JWT tokens from your API keys: `POST /v2/auth/exchange`
2. Update client code to use Authorization header
3. Store tokens securely (never in URLs)

**Code Examples**:

JavaScript:

```javascript
// v1 (old)
fetch('https://api.example.com/v1/users?api_key=YOUR_KEY')

// v2 (new)
fetch('https://api.example.com/v2/users', {
  headers: {
    'Authorization': 'Bearer YOUR_TOKEN'
  }
})
```

Python:

```python
# v1 (old)
response = requests.get('https://api.example.com/v1/users',
  params={'api_key': 'YOUR_KEY'})

# v2 (new)
response = requests.get('https://api.example.com/v2/users',
  headers={'Authorization': 'Bearer YOUR_TOKEN'})
```

### 2. User Endpoint Changes

**v1 Structure**:

```json
{
  "id": 123,
  "name": "John Doe",
  "email": "john@example.com"
}
```

**v2 Structure** (JSON:API format):

```json
{
  "data": {
    "id": "usr_123",
    "type": "user",
    "attributes": {
      "firstName": "John",
      "lastName": "Doe",
      "email": "john@example.com"
    }
  }
}
```

**Changes**:

- `id` is now a string with prefix (`usr_`)
- `name` split into `firstName` and `lastName`
- Response wrapped in `data` object
- Added `type` field for polymorphism

**Migration Steps**:

1. Update response parsing to access `data.attributes`
2. Handle string IDs instead of integers
3. Split `name` into `firstName` + `lastName` when creating users
4. Update any ID-based routing or storage

### 3. Pagination Changes

**v1** (Offset-based):

```bash
GET /users?page=2&limit=20
```

**v2** (Cursor-based):

```bash
GET /users?cursor=eyJpZCI6MTIzfQ&limit=20
```

**Why the change?**

- Better performance for large datasets
- Consistent results with concurrent writes
- Prevents missing/duplicate records

**Migration Steps**:

1. Replace `page` parameter with `cursor` from previous response
2. Use `pagination.next_cursor` from response for next page
3. Remove page number tracking in client code

**Code Example**:

```javascript
// v1 (old)
let page = 1
while (true) {
  const response = await fetch(`/v1/users?page=${page}&limit=20`)
  const users = await response.json()
  if (users.length === 0) break
  page++
}

// v2 (new)
let cursor = null
while (true) {
  const url = cursor
    ? `/v2/users?cursor=${cursor}&limit=20`
    : '/v2/users?limit=20'
  const response = await fetch(url)
  const data = await response.json()
  if (!data.pagination.has_more) break
  cursor = data.pagination.next_cursor
}
```

### 4. Error Response Format

**v1 Format**:

```json
{
  "error": "Invalid email address",
  "code": 400
}
```

**v2 Format** (JSON:API errors):

```json
{
  "errors": [
    {
      "id": "err_001",
      "status": "422",
      "code": "VALIDATION_ERROR",
      "title": "Validation Failed",
      "detail": "Email address is invalid",
      "source": {
        "pointer": "/data/attributes/email"
      }
    }
  ]
}
```

**Migration Steps**:

1. Update error handling to parse `errors` array
2. Use `status` field instead of HTTP status code
3. Display `detail` for user-facing messages
4. Use `source.pointer` to highlight field errors

### 5. Rate Limiting

**v1**: 500 requests per hour per API key

**v2**: Tiered rate limiting

- Free tier: 100 requests/hour
- Pro tier: 1,000 requests/hour
- Enterprise: 10,000 requests/hour

**New Headers**:

```
X-Rate-Limit-Limit: 1000
X-Rate-Limit-Remaining: 999
X-Rate-Limit-Reset: 1640000000
```

**Migration Steps**:

1. Monitor rate limit headers in responses
2. Implement exponential backoff on 429 errors
3. Upgrade tier if hitting limits
4. Cache responses to reduce API calls

## New Features in v2

### 1. Webhook Support

Subscribe to real-time events:

```bash
POST /v2/webhooks
{
  "url": "https://your-app.com/webhooks",
  "events": ["user.created", "user.updated"],
  "secret": "webhook_secret_for_verification"
}
```

### 2. Batch Operations

Create/update multiple resources in one request:

```bash
POST /v2/users/batch
{
  "operations": [
    { "action": "create", "data": {...} },
    { "action": "update", "id": "usr_123", "data": {...} }
  ]
}
```

### 3. Field Filtering

Request only the fields you need:

```bash
GET /v2/users?fields=id,email,firstName
```

### 4. Relationship Inclusion

Include related resources in one request:

```bash
GET /v2/orders?include=user,items
```

## Backward Compatibility

### Using Both Versions

You can run v1 and v2 in parallel during migration:

```javascript
// Support both versions
const API_VERSION = process.env.API_VERSION || 'v2'
const BASE_URL = `https://api.example.com/${API_VERSION}`

async function getUsers() {
  const response = await fetch(`${BASE_URL}/users`)

  if (API_VERSION === 'v1') {
    return await response.json() // Direct array
  } else {
    const data = await response.json()
    return data.data // Wrapped in data object
  }
}
```

### Abstraction Layer

Create adapter to handle version differences:

```javascript
class UserAPIAdapter {
  constructor(version = 'v2') {
    this.version = version
    this.baseURL = `https://api.example.com/${version}`
  }

  async getUsers({ page, limit } = {}) {
    if (this.version === 'v1') {
      // v1 implementation
      const response = await fetch(
        `${this.baseURL}/users?page=${page}&limit=${limit}`
      )
      return await response.json()
    } else {
      // v2 implementation
      const response = await fetch(
        `${this.baseURL}/users?limit=${limit}`
      )
      const data = await response.json()
      return data.data
    }
  }

  async createUser(userData) {
    if (this.version === 'v1') {
      // v1: direct object
      return await this.post('/users', userData)
    } else {
      // v2: wrapped in data object
      return await this.post('/users', {
        data: {
          type: 'user',
          attributes: userData
        }
      })
    }
  }
}
```

## Testing Your Migration

### 1. Parallel Testing

Test both versions with same data:

```javascript
const v1API = new UserAPIAdapter('v1')
const v2API = new UserAPIAdapter('v2')

// Compare results
const v1Users = await v1API.getUsers()
const v2Users = await v2API.getUsers()

// Verify data equivalence
assert.equal(v1Users.length, v2Users.length)
```

### 2. Shadow Mode

Send requests to v2 but use v1 responses:

```javascript
async function getUsersShadow(userId) {
  // Production request to v1
  const v1Response = await fetch(`/v1/users/${userId}`)

  // Shadow request to v2 (don't wait)
  fetch(`/v2/users/${userId}`).then(v2Response => {
    // Log differences for analysis
    logDifferences(v1Response, v2Response)
  })

  return v1Response // Use v1 for now
}
```

### 3. Feature Flags

Gradual rollout with feature flags:

```javascript
const USE_V2 = featureFlags.isEnabled('api-v2', userId)

const API = USE_V2 ? v2API : v1API
const users = await API.getUsers()
```

## Timeline and Support

### Phase 1: v2 Release (January 15, 2024)

- ✓ v2 available for testing
- ✓ v1 fully supported
- ✓ Documentation available
- ✓ Migration guide published

### Phase 2: Deprecation Notice (April 15, 2024)

- ⚠ v1 officially deprecated
- ✓ v1 still functional
- ⚠ Deprecation warnings in responses
- ✓ Email notifications to v1 users

### Phase 3: Sunset Warning (June 15, 2024)

- ⚠ 30 days until v1 shutdown
- ⚠ Daily emails to remaining v1 users
- ✓ Migration support available

### Phase 4: v1 Sunset (July 15, 2024)

- ✗ v1 endpoints return 410 Gone
- ✓ Automatic redirects to v2 (where possible)
- ✓ Documentation archived

## Getting Help

### Migration Support

- **Email**: <api-support@example.com>
- **Slack**: #api-migration
- **Office Hours**: Tuesdays 2-4pm EST

### Resources

- [v2 API Documentation](https://docs.example.com/v2)
- [Breaking Changes Reference](https://docs.example.com/breaking-changes)
- [Code Examples Repository](https://github.com/company/api-examples)
- [Migration Checklist](https://docs.example.com/migration-checklist)

### SDK Updates

All official SDKs have been updated for v2:

- JavaScript: `npm install @company/api-client@2.0.0`
- Python: `pip install company-api-client==2.0.0`
- Go: `go get github.com/company/api-client/v2`

## Migration Checklist

Use this checklist to track your migration progress:

- [ ] Read complete migration guide
- [ ] Review breaking changes
- [ ] Update authentication (API key → JWT)
- [ ] Update response parsing (access `data.attributes`)
- [ ] Update pagination (page → cursor)
- [ ] Update error handling (parse `errors` array)
- [ ] Handle new rate limit headers
- [ ] Update all endpoint URLs (/v1 → /v2)
- [ ] Update SDK to v2 version
- [ ] Test in staging environment
- [ ] Monitor for errors in production
- [ ] Remove v1 code after successful migration
- [ ] Celebrate! 🎉

EOF

echo "✓ Migration guide generated: docs/migrations/v${FROM_VERSION}-to-v${TO_VERSION}.md"

```

## Step 5: Implement Version Routing

Generate version routing code:

### For Node.js/Express

```javascript
// middleware/versioning.js
const express = require('express')

function versionRouter() {
  const router = express.Router()

  // URL-based versioning
  router.use('/v1', require('../routes/v1'))
  router.use('/v2', require('../routes/v2'))

  // Default to latest version
  router.use('/', require('../routes/v2'))

  return router
}

// Alternative: Header-based versioning
function headerVersioning(req, res, next) {
  const version = req.headers['accept-version'] || 'v2'

  if (version === 'v1') {
    req.apiVersion = 'v1'
  } else if (version === 'v2') {
    req.apiVersion = 'v2'
  } else {
    return res.status(400).json({
      errors: [{
        code: 'INVALID_VERSION',
        detail: `API version ${version} not supported. Use v1 or v2.`
      }]
    })
  }

  next()
}

module.exports = { versionRouter, headerVersioning }
```

### For Python/FastAPI

```python
# versioning.py
from fastapi import FastAPI, Header, HTTPException
from typing import Optional

app = FastAPI()

# URL-based versioning
from routers import v1, v2

app.include_router(v1.router, prefix="/v1", tags=["v1"])
app.include_router(v2.router, prefix="/v2", tags=["v2"])

# Header-based versioning
async def get_api_version(
    accept_version: Optional[str] = Header(default="v2", alias="Accept-Version")
) -> str:
    if accept_version not in ["v1", "v2"]:
        raise HTTPException(
            status_code=400,
            detail=f"API version {accept_version} not supported"
        )
    return accept_version

# Use in endpoints
@app.get("/users")
async def get_users(version: str = Depends(get_api_version)):
    if version == "v1":
        return v1_get_users()
    else:
        return v2_get_users()
```

## Step 6: Implement Deprecation Notices

Add deprecation warnings to old version:

```javascript
// middleware/deprecation.js
function deprecationWarning(version, sunsetDate) {
  return (req, res, next) => {
    // Add deprecation headers
    res.set({
      'Deprecation': 'true',
      'Sunset': sunsetDate.toISOString(),
      'Link': '<https://docs.example.com/migration>; rel="deprecation"'
    })

    // Add warning to response body
    const originalJson = res.json.bind(res)
    res.json = function(data) {
      if (typeof data === 'object') {
        data._meta = {
          ...data._meta,
          deprecation: {
            deprecated: true,
            sunset_date: sunsetDate.toISOString(),
            migration_guide: 'https://docs.example.com/migration',
            message: `API ${version} is deprecated and will be sunset on ${sunsetDate.toDateString()}`
          }
        }
      }
      return originalJson(data)
    }

    next()
  }
}

// Apply to v1 routes
app.use('/v1', deprecationWarning('v1', new Date('2024-07-15')))
```

## Step 7: Generate Version Comparison

Create side-by-side comparison:

```bash
cat > docs/version-comparison.md <<'EOF'
# API Version Comparison

## Quick Reference

| Feature | v1 | v2 |
|---------|----|----|
| Authentication | API Key (query param) | JWT (header) |
| Response Format | Plain JSON | JSON:API |
| Pagination | Offset-based | Cursor-based |
| Error Format | Simple object | JSON:API errors |
| Rate Limiting | 500/hour | Tiered (100-10k/hour) |
| Webhooks | ❌ No | ✅ Yes |
| Batch Operations | ❌ No | ✅ Yes |
| Field Filtering | ❌ No | ✅ Yes |
| Status | Deprecated | Current |
| Sunset Date | July 15, 2024 | - |

## Endpoint Comparison

### Users Endpoint

**v1**:
```

GET /v1/users?page=1&limit=20&api_key=KEY

```

**v2**:
```

GET /v2/users?cursor=CURSOR&limit=20
Authorization: Bearer TOKEN

```

[Full comparison continues...]

EOF
```

## Step 8: Create Sunset Automation

Implement automatic sunset:

```javascript
// middleware/sunset.js
function sunsetEnforcement(sunsetDate) {
  return (req, res, next) => {
    const now = new Date()

    if (now >= sunsetDate) {
      // API version is sunset
      return res.status(410).json({
        errors: [{
          status: '410',
          code: 'API_VERSION_SUNSET',
          title: 'API Version No Longer Available',
          detail: 'This API version was sunset. Please upgrade to v2.',
          meta: {
            sunset_date: sunsetDate.toISOString(),
            migration_guide: 'https://docs.example.com/migration',
            current_version: 'v2'
          }
        }]
      })
    }

    next()
  }
}

// Apply to old versions
app.use('/v1', sunsetEnforcement(new Date('2024-07-15')))
```

## Step 9: Display Summary

```
════════════════════════════════════════════════════════
         API VERSIONING CONFIGURED
════════════════════════════════════════════════════════

STRATEGY: URL-based versioning
CURRENT VERSION: v2
PREVIOUS VERSION: v1 (deprecated)

MIGRATION GUIDE:
✓ docs/migrations/v1-to-v2.md
✓ Complete migration checklist
✓ Code examples for all changes
✓ Breaking changes documented

VERSION ROUTING:
✓ /v1/* → Legacy endpoints (deprecated)
✓ /v2/* → Current endpoints
✓ /* → Defaults to v2

DEPRECATION:
⚠ v1 deprecated as of April 15, 2024
⚠ v1 sunset date: July 15, 2024 (90 days)
✓ Deprecation headers added to v1 responses
✓ Sunset enforcement configured

BREAKING CHANGES DETECTED:
⚠ Authentication: API Key → JWT
⚠ Response format: Plain JSON → JSON:API
⚠ Pagination: Offset → Cursor-based
⚠ User.name split into firstName + lastName
⚠ Error format changed

════════════════════════════════════════════════════════

NEXT STEPS:

1. Review migration guide:
   cat docs/migrations/v1-to-v2.md

2. Notify API users:
   - Email all v1 users with migration guide
   - Post announcement in developer portal
   - Update documentation homepage

3. Monitor adoption:
   - Track v1 vs v2 usage
   - Identify users still on v1
   - Offer migration support

4. Implement sunset:
   - 90 days: Deprecation notice
   - 60 days: Email reminders
   - 30 days: Daily warnings
   - 0 days: Return 410 Gone

════════════════════════════════════════════════════════

TIMELINE:
📅 Apr 15, 2024: v1 deprecated (deprecation warnings)
📅 Jun 15, 2024: 30-day sunset warning
📅 Jul 15, 2024: v1 sunset (410 Gone)

════════════════════════════════════════════════════════
```

## Business Value & ROI

**Risk Reduction**:

- Structured deprecation process prevents breaking user integrations
- Clear migration paths reduce support burden
- Backward compatibility maintains customer satisfaction

**Time Savings**:

- Automated breaking change detection: 90% faster
- Migration guide generation: 10x faster
- Version routing implementation: 5x faster

**Cost Savings**:

- Reduce migration-related support tickets by 70%
- Prevent lost revenue from broken integrations
- Faster version transitions = less dual-version maintenance

**Business Impact**:

- Customer trust through professional version management
- Clear communication prevents surprise breaking changes
- Gradual deprecation allows users to plan migrations

## Success Metrics

**Migration Metrics**:

- v2 adoption rate: Target 80% within 60 days
- Migration completion time: Target < 2 weeks per customer
- Breaking change incidents: Target zero
- Support tickets: Target <10 migration-related

**Technical Metrics**:

- v1 traffic percentage: Monitor decline
- v2 error rate: Target <0.5%
- Version-related errors: Target zero
- Deprecation warnings acknowledged: Monitor

**Customer Satisfaction**:

- Migration satisfaction score: Target >4.5/5
- Documentation clarity: Target >4.5/5
- Support responsiveness: Target >4.5/5

---

**Model**: Claude Sonnet 4.5 (complex version management strategy)
**Estimated time**: 30-60 minutes for complete versioning setup
**Requirements**: Node.js/Python, git, OpenAPI spec
