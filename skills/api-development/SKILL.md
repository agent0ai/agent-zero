---
name: "api-development"
description: "Best practices for designing and implementing RESTful and GraphQL APIs. Use when building, designing, or reviewing APIs."
version: "1.0.0"
author: "Agent Zero Team"
tags: ["api", "rest", "graphql", "design", "backend", "web"]
trigger_patterns:
  - "api"
  - "endpoint"
  - "rest"
  - "graphql"
  - "http"
---

# API Development Skill

Best practices for designing, implementing, and documenting APIs.

## RESTful API Design

### URL Structure

```
https://api.example.com/v1/resources/{id}/subresources
```

**Guidelines:**
- Use nouns, not verbs: `/users` not `/getUsers`
- Use plural nouns: `/users` not `/user`
- Use kebab-case: `/user-profiles` not `/userProfiles`
- Nest resources logically: `/users/{id}/orders`
- Version your API: `/v1/`, `/v2/`

### HTTP Methods

| Method | Purpose | Example |
|--------|---------|---------|
| `GET` | Retrieve resource(s) | `GET /users/123` |
| `POST` | Create resource | `POST /users` |
| `PUT` | Replace resource | `PUT /users/123` |
| `PATCH` | Partial update | `PATCH /users/123` |
| `DELETE` | Remove resource | `DELETE /users/123` |

### Status Codes

| Code | Meaning | When to Use |
|------|---------|-------------|
| `200 OK` | Success | GET, PUT, PATCH success |
| `201 Created` | Resource created | POST success |
| `204 No Content` | Success, no body | DELETE success |
| `400 Bad Request` | Invalid input | Validation failed |
| `401 Unauthorized` | Not authenticated | Missing/invalid token |
| `403 Forbidden` | Not authorized | Insufficient permissions |
| `404 Not Found` | Resource not found | ID doesn't exist |
| `409 Conflict` | Resource conflict | Duplicate entry |
| `422 Unprocessable` | Semantic error | Valid syntax, invalid data |
| `429 Too Many` | Rate limited | Exceeded request limit |
| `500 Server Error` | Internal error | Unexpected failure |

### Request/Response Format

**Request:**
```http
POST /api/v1/users HTTP/1.1
Content-Type: application/json
Authorization: Bearer <token>

{
  "email": "user@example.com",
  "name": "John Doe",
  "role": "user"
}
```

**Success Response:**
```json
{
  "data": {
    "id": "123",
    "email": "user@example.com",
    "name": "John Doe",
    "role": "user",
    "created_at": "2024-01-15T10:30:00Z"
  },
  "meta": {
    "request_id": "abc-123"
  }
}
```

**Error Response:**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": [
      {
        "field": "email",
        "message": "Invalid email format"
      }
    ]
  },
  "meta": {
    "request_id": "abc-123"
  }
}
```

### Pagination

**Request:**
```http
GET /api/v1/users?page=2&per_page=20
```

**Response:**
```json
{
  "data": [...],
  "meta": {
    "current_page": 2,
    "per_page": 20,
    "total_pages": 10,
    "total_count": 195
  },
  "links": {
    "first": "/api/v1/users?page=1&per_page=20",
    "prev": "/api/v1/users?page=1&per_page=20",
    "next": "/api/v1/users?page=3&per_page=20",
    "last": "/api/v1/users?page=10&per_page=20"
  }
}
```

### Filtering & Sorting

```http
# Filtering
GET /api/v1/users?status=active&role=admin

# Sorting
GET /api/v1/users?sort=created_at&order=desc

# Multiple sort fields
GET /api/v1/users?sort=-created_at,name
```

### Field Selection

```http
GET /api/v1/users?fields=id,name,email
```

## Authentication

### JWT (JSON Web Token)

```javascript
// Token structure
{
  "header": {
    "alg": "HS256",
    "typ": "JWT"
  },
  "payload": {
    "sub": "user_123",
    "email": "user@example.com",
    "role": "admin",
    "iat": 1516239022,
    "exp": 1516242622
  },
  "signature": "..."
}
```

**Implementation:**

```python
# Python example with PyJWT
import jwt
from datetime import datetime, timedelta

def create_token(user_id: str, secret: str) -> str:
    payload = {
        "sub": user_id,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(payload, secret, algorithm="HS256")

def verify_token(token: str, secret: str) -> dict:
    try:
        return jwt.decode(token, secret, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise AuthError("Token expired")
    except jwt.InvalidTokenError:
        raise AuthError("Invalid token")
```

### API Keys

```http
# Header
Authorization: Api-Key <key>

# Query param (less secure)
GET /api/v1/resource?api_key=<key>
```

## Rate Limiting

**Headers:**
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1609459200
```

**Implementation:**
```python
from functools import wraps
import time

class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window = window_seconds
        self.requests = {}

    def is_allowed(self, client_id: str) -> bool:
        now = time.time()
        window_start = now - self.window

        # Clean old requests
        self.requests[client_id] = [
            t for t in self.requests.get(client_id, [])
            if t > window_start
        ]

        if len(self.requests[client_id]) >= self.max_requests:
            return False

        self.requests[client_id].append(now)
        return True
```

## Input Validation

```python
from pydantic import BaseModel, EmailStr, validator

class CreateUserRequest(BaseModel):
    email: EmailStr
    name: str
    age: int

    @validator('name')
    def name_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip()

    @validator('age')
    def age_valid(cls, v):
        if v < 0 or v > 150:
            raise ValueError('Age must be between 0 and 150')
        return v
```

## Error Handling

```python
class APIError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code

@app.errorhandler(APIError)
def handle_api_error(error):
    return jsonify({
        "error": {
            "code": error.code,
            "message": error.message
        }
    }), error.status_code

# Usage
raise APIError("USER_NOT_FOUND", "User with ID 123 not found", 404)
```

## API Documentation

### OpenAPI/Swagger Example

```yaml
openapi: 3.0.0
info:
  title: User API
  version: 1.0.0

paths:
  /users:
    get:
      summary: List all users
      parameters:
        - name: page
          in: query
          schema:
            type: integer
            default: 1
      responses:
        '200':
          description: Successful response
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UserList'
    post:
      summary: Create a user
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateUser'
      responses:
        '201':
          description: User created

components:
  schemas:
    User:
      type: object
      properties:
        id:
          type: string
        email:
          type: string
        name:
          type: string
```

## Security Checklist

```markdown
- [ ] Use HTTPS only
- [ ] Validate all input
- [ ] Sanitize output
- [ ] Use parameterized queries
- [ ] Implement rate limiting
- [ ] Use secure headers (CORS, CSP)
- [ ] Don't expose internal errors
- [ ] Log security events
- [ ] Rotate secrets regularly
- [ ] Version your API
```

## Performance Tips

1. **Use caching headers**
   ```http
   Cache-Control: max-age=3600
   ETag: "abc123"
   ```

2. **Implement compression**
   ```http
   Accept-Encoding: gzip
   Content-Encoding: gzip
   ```

3. **Use pagination** for large datasets

4. **Implement field selection** to reduce payload

5. **Consider async processing** for long operations
   ```json
   {
     "status": "processing",
     "job_id": "job_123",
     "check_url": "/api/v1/jobs/job_123"
   }
   ```
