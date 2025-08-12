---
source: https://learn.microsoft.com/en-us/azure/architecture/best-practices/api-design
retrieved: 2025-08-09T14:33:24Z
fetch_method: document_query
agent: agent0
original_filename: rest_api_design_best_practices_microsoft_azure.md
content_type: technical_guide
verification_status: pending
---

# Web API Design Best Practices - Azure Architecture Center

*Source: Microsoft Learn - Azure Architecture Center*

## Overview

This comprehensive guide from Microsoft Azure Architecture Center covers best practices for designing RESTful web APIs. It provides authoritative guidance on implementing REST architectural principles to achieve stateless, loosely coupled interfaces between clients and services.

## RESTful Web API Design Principles

A RESTful web API implementation should align with the following core principles:

### Platform Independence
- Clients can call the web API regardless of internal implementation
- Uses HTTP as a standard protocol
- Provides clear documentation
- Supports familiar data exchange formats (JSON, XML)

### Loose Coupling
- Client and web service can evolve independently
- Client doesn't need to know internal implementation of web service
- Web service doesn't need to know internal implementation of client
- Uses only standard protocols
- Implements mechanisms for client-service data format agreement

## Core RESTful Web API Design Concepts

### 1. Uniform Resource Identifier (URI)

REST APIs are designed around **resources** - any kind of object, data, or service that clients can access. Each resource is represented by a URI that uniquely identifies that resource.

**Example:**
```
https://api.contoso.com/orders/1
```

### 2. Resource Representation

Defines how a resource identified by its URI is encoded and transported over HTTP in a specific format (XML, JSON).

**Example GET Response:**
```json
{"orderId":1,"orderValue":99.9,"productId":1,"quantity":1}
```

### 3. Uniform Interface

Achieves loose coupling between client and service implementations using standard HTTP verbs:
- `GET` - Retrieve resources
- `POST` - Create new resources
- `PUT` - Update existing resources
- `PATCH` - Partial updates
- `DELETE` - Remove resources

### 4. Stateless Request Model

- HTTP requests are independent and can occur in any order
- No transient state information stored between requests
- Information stored only in resources themselves
- Each request should be atomic
- Supports high scalability (no client-server affinity required)

### 5. Hypermedia Links (HATEOAS)

REST APIs can be driven by hypermedia links contained in each resource representation.

**Example:**
```json
{
  "orderID":3,
  "productID":2,
  "quantity":4,
  "orderValue":16.60,
  "links": [
    {"rel":"product","href":"https://api.contoso.com/customers/3", "action":"GET" },
    {"rel":"product","href":"https://api.contoso.com/customers/3", "action":"PUT" }
  ]
}
```

## Defining RESTful Web API Resource URIs

### Resource-Oriented Design

Organize API design around resources that map to business entities. Base resource URIs on **nouns** (the resource) rather than **verbs** (operations).

**Good Examples:**
```
https://api.contoso.com/orders        // Collection
https://api.contoso.com/orders/1      // Individual item
https://api.contoso.com/customers     // Collection
https://api.contoso.com/customers/5   // Individual item
```

**Avoid:**
```
https://api.contoso.com/create-order  // Verb-based (avoid)
https://api.contoso.com/get-customer  // Verb-based (avoid)
```

### Resource URI Naming Conventions

#### 1. Use Nouns for Resource Names
- Use `/orders` instead of `/create-order`
- HTTP methods already imply the verbal action
- Focus on what the resource represents, not what you do with it

#### 2. Use Plural Nouns for Collections
- `/customers` for the customer collection
- `/customers/5` for customer with ID 5
- Organize URIs for collections and items into hierarchies
- Many frameworks can route requests based on parameterized URI paths (`/customers/{id}`)

#### 3. Consider Resource Relationships

Represent associations between different resource types:

**Examples:**
```
/customers/5/orders           // All orders for customer 5
/orders/99/customer          // Customer associated with order 99
/customers/1/orders/99/products  // Products in order 99 for customer 1
```

**Best Practice:** Keep relationships simple and flexible. Avoid URIs more complex than `collection/item/collection`.

#### 4. Avoid Chatty APIs

- Don't expose large numbers of small resources
- Consider denormalizing data and combining related information
- Balance against overhead of fetching unneeded data
- Each web request imposes server load

#### 5. Don't Mirror Database Structure

- REST models business entities, not database tables
- Don't expose internal implementation details
- Use mapping layer between database and web API if necessary
- Protect against data leakage and increased attack surface

## RESTful Web API Methods

### HTTP Request Methods Overview

The following table shows conventions for HTTP methods on collections vs. individual items:

| **Resource** | **POST** | **GET** | **PUT** | **DELETE** |
|--------------|----------|---------|---------|------------|
| /customers | Create new customer | Retrieve all customers | Bulk update customers | Remove all customers |
| /customers/1 | Error | Retrieve customer 1 details | Update customer 1 | Remove customer 1 |
| /customers/1/orders | Create order for customer 1 | Retrieve all orders for customer 1 | Bulk update orders | Remove all orders |

### GET Requests

**Purpose:** Retrieve resource representation

**Response Codes:**
- `200 (OK)` - Successfully returned resource
- `204 (No Content)` - No content (e.g., empty search results)
- `404 (Not Found)` - Resource doesn't exist

**Example:**
```http
GET /api/customers/1
Response: {"id":1,"name":"John Doe","email":"john@example.com"}
```

### POST Requests

**Purpose:** Create new resources

**Key Points:**
- Server assigns URI for new resource
- Client submits to collection URI
- Client should NOT create its own URI

**Response Codes:**
- `200 (OK)` - Processing completed, no new resource created
- `201 (Created)` - Resource created successfully (include Location header)
- `204 (No Content)` - No content in response body
- `400 (Bad Request)` - Invalid data in request
- `405 (Method Not Allowed)` - POST not supported on this URI

**Example:**
```http
POST /api/customers
Content-Type: application/json

{"name":"Jane Smith","email":"jane@example.com"}

Response:
201 Created
Location: /api/customers/123
{"id":123,"name":"Jane Smith","email":"jane@example.com"}
```

### PUT Requests

**Purpose:** Update existing resource or create if it doesn't exist

**Key Characteristics:**
- **Idempotent** - Multiple identical requests have same effect
- Client specifies complete resource representation
- Applied to individual items, not collections

**Response Codes:**
- `200 (OK)` - Resource updated successfully
- `201 (Created)` - Resource created successfully
- `204 (No Content)` - Updated successfully, no content returned
- `409 (Conflict)` - Conflict with current resource state

**Example:**
```http
PUT /api/customers/123
Content-Type: application/json

{"id":123,"name":"Jane Smith Updated","email":"jane.updated@example.com"}
```

### PATCH Requests

**Purpose:** Partial update to existing resource

**Key Points:**
- More efficient than PUT (send only changes)
- Can create new resource if server supports it
- Not guaranteed to be idempotent

**JSON Merge Patch Example:**
```http
PATCH /api/customers/123
Content-Type: application/merge-patch+json

{
    "email":"new.email@example.com",
    "phone":null,
    "address":"123 New Street"
}
```

**JSON Patch Example:**
```http
PATCH /api/customers/123
Content-Type: application/json-patch+json

[
  { "op": "replace", "path": "/email", "value": "new.email@example.com" },
  { "op": "remove", "path": "/phone" },
  { "op": "add", "path": "/address", "value": "123 New Street" }
]
```

**Response Codes:**
- `200 (OK)` - Resource updated successfully
- `400 (Bad Request)` - Malformed patch document
- `409 (Conflict)` - Valid patch but can't be applied
- `415 (Unsupported Media Type)` - Patch format not supported

### DELETE Requests

**Purpose:** Remove resource

**Response Codes:**
- `204 (No Content)` - Resource deleted successfully
- `404 (Not Found)` - Resource doesn't exist

**Example:**
```http
DELETE /api/customers/123

Response:
204 No Content
```

## Resource MIME Types

Resource representations are specified using media types (MIME types):

### Common Media Types
- **JSON:** `application/json` (most common)
- **XML:** `application/xml`
- **Custom:** `application/vnd.company.v1+json`

### Content Negotiation

**Request with Content-Type:**
```http
POST /api/orders
Content-Type: application/json; charset=utf-8

{"productId":1,"quantity":2}
```

**Request with Accept Header:**
```http
GET /api/orders/1
Accept: application/json, application/xml
```

**Response Codes:**
- `415 (Unsupported Media Type)` - Server doesn't support request media type
- `406 (Not Acceptable)` - Server can't provide requested response format

## Asynchronous Operations

For long-running operations, implement asynchronous patterns:

### Initial Request
```http
POST /api/orders/bulk-import
Content-Type: application/json

{"fileUrl":"https://example.com/orders.csv"}

Response:
202 Accepted
Location: /api/status/12345
```

### Status Polling
```http
GET /api/status/12345

Response:
200 OK
Content-Type: application/json

{
    "status":"In progress",
    "progress":"45%",
    "estimatedCompletion":"2025-08-09T15:30:00Z",
    "link": { 
        "rel":"cancel", 
        "method":"DELETE", 
        "href":"/api/status/12345" 
    }
}
```

### Completion
```http
GET /api/status/12345

Response:
303 See Other
Location: /api/orders/batch/67890
```

## Data Pagination and Filtering

### Pagination

Implement pagination for large datasets:

```http
GET /api/orders?limit=25&offset=50
```

**Parameters:**
- `limit` - Maximum number of items to return
- `offset` - Starting index for data
- Consider imposing upper limits (e.g., max 100 items)

**Response with Pagination Metadata:**
```json
{
  "data": [...],
  "pagination": {
    "limit": 25,
    "offset": 50,
    "total": 1000,
    "hasMore": true,
    "nextUrl": "/api/orders?limit=25&offset=75"
  }
}
```

### Filtering and Sorting

```http
GET /api/orders?status=shipped&minAmount=100&sort=createdDate&fields=id,total,status
```

**Query Parameters:**
- `status=shipped` - Filter by status
- `minAmount=100` - Filter by minimum amount
- `sort=createdDate` - Sort by creation date
- `fields=id,total,status` - Return only specified fields

**Best Practices:**
- Validate all query parameters
- Ensure client is authorized to access requested fields
- Consider caching implications of query parameters

## Partial Responses for Large Resources

Support partial retrieval for large binary resources:

### HEAD Request for Resource Info
```http
HEAD /api/products/10/image

Response:
200 OK
Accept-Ranges: bytes
Content-Type: image/jpeg
Content-Length: 4580
```

### Partial GET Request
```http
GET /api/products/10/image
Range: bytes=0-2499

Response:
206 Partial Content
Accept-Ranges: bytes
Content-Type: image/jpeg
Content-Length: 2500
Content-Range: bytes 0-2499/4580

[binary data]
```

## HATEOAS Implementation

Hypertext as the Engine of Application State enables API discoverability:

### Resource with Hypermedia Links
```json
{
  "orderID":3,
  "productID":2,
  "quantity":4,
  "orderValue":16.60,
  "links":[
    {
      "rel":"customer",
      "href":"https://api.contoso.com/customers/3",
      "action":"GET",
      "types":["text/xml","application/json"]
    },
    {
      "rel":"customer",
      "href":"https://api.contoso.com/customers/3",
      "action":"PUT",
      "types":["application/x-www-form-urlencoded"]
    },
    {
      "rel":"self",
      "href":"https://api.contoso.com/orders/3",
      "action":"GET",
      "types":["text/xml","application/json"]
    }
  ]
}
```

### Benefits of HATEOAS
- Clients can navigate API without prior knowledge of URI schema
- API becomes self-documenting
- Reduces coupling between client and server
- Enables dynamic API discovery

## API Versioning Strategies

### 1. URI Versioning

```http
GET /api/v1/customers/3
GET /api/v2/customers/3
```

**Pros:**
- Simple and explicit
- Easy to implement
- Clear version separation

**Cons:**
- Violates REST principle (same resource, different URIs)
- Complicates HATEOAS implementation
- Can become unwieldy with many versions

### 2. Query String Versioning

```http
GET /api/customers/3?version=2
```

**Pros:**
- Same resource URI
- Easy to implement

**Cons:**
- May not be cached by older browsers/proxies
- Complicates HATEOAS
- Version parameter parsing required

### 3. Header Versioning

```http
GET /api/customers/3
API-Version: 2
```

**Pros:**
- Clean URIs
- Flexible versioning

**Cons:**
- Less visible than URI versioning
- Requires custom header handling
- Complicates caching

### 4. Media Type Versioning

```http
GET /api/customers/3
Accept: application/vnd.contoso.v2+json

Response:
Content-Type: application/vnd.contoso.v2+json
```

**Pros:**
- Follows HTTP standards
- Good for HATEOAS
- Flexible content negotiation

**Cons:**
- More complex implementation
- Requires understanding of media types
- Can complicate caching

### Versioning Best Practices

1. **Choose one strategy and be consistent**
2. **Support multiple versions simultaneously**
3. **Provide clear migration paths**
4. **Document version differences**
5. **Consider backward compatibility**
6. **Plan deprecation strategy**

## Multitenant Web APIs

Multitenancy affects API design for shared resources across multiple tenants:

### 1. Subdomain-Based Isolation

```http
GET https://tenant1.api.contoso.com/orders/3
GET https://tenant2.api.contoso.com/orders/3
```

**Benefits:**
- Clear tenant separation
- DNS-level routing
- Custom domain support

**Considerations:**
- DNS configuration complexity
- SSL certificate management
- Hostname preservation requirements

### 2. Header-Based Tenancy

```http
GET https://api.contoso.com/orders/3
X-Tenant-ID: tenant1
```

**Benefits:**
- Centralized authentication
- Dynamic tenant context
- Cleaner API design

**Considerations:**
- Layer 7 routing required
- Caching complications
- Data leakage risks if not properly implemented

### 3. Path-Based Tenancy

```http
GET https://api.contoso.com/tenants/tenant1/orders/3
```

**Benefits:**
- Explicit tenant identification
- URI-based routing

**Considerations:**
- Compromises RESTful design
- Complex routing logic
- Pattern matching requirements

## Distributed Tracing and Observability

Enable end-to-end request tracking:

### Correlation Headers

```http
GET /api/orders/3
Correlation-ID: aaaa0000-bb11-2222-33cc-444444dddddd
X-Request-ID: req-12345
X-Trace-ID: trace-67890

Response:
200 OK
Correlation-ID: aaaa0000-bb11-2222-33cc-444444dddddd
X-Request-ID: req-12345

{"orderId":3,...}
```

### Benefits
- End-to-end request tracking
- Rapid failure identification
- Latency monitoring
- Service dependency mapping
- Enhanced debugging capabilities

## Richardson Maturity Model (RMM)

The Richardson Maturity Model defines four levels of REST API maturity:

### Level 0: The Swamp of POX (Plain Old XML)
- Single URI endpoint
- All operations use POST
- Example: SOAP web services

### Level 1: Resources
- Multiple URIs for different resources
- Still uses single HTTP method (usually POST)
- Beginning to align with RESTful design

### Level 2: HTTP Verbs
- Uses HTTP methods to define operations
- GET, POST, PUT, DELETE for different actions
- Most published web APIs align with this level

### Level 3: Hypermedia Controls (HATEOAS)
- Uses hypermedia links for API navigation
- Truly RESTful according to Fielding's definition
- Self-documenting and discoverable API

## OpenAPI Initiative and Specification

The OpenAPI Specification (formerly Swagger) standardizes REST API descriptions:

### Benefits of OpenAPI
- Standardized API documentation
- Code generation capabilities
- Contract-first development approach
- Tool ecosystem support
- Industry-wide interoperability

### OpenAPI Example
```yaml
openapi: 3.0.0
info:
  title: Orders API
  version: 1.0.0
paths:
  /orders:
    get:
      summary: List orders
      parameters:
        - name: limit
          in: query
          schema:
            type: integer
            default: 25
      responses:
        '200':
          description: List of orders
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/Order'
components:
  schemas:
    Order:
      type: object
      properties:
        id:
          type: integer
        total:
          type: number
        status:
          type: string
```

### Contract-First Development
1. Design API contract (OpenAPI specification)
2. Generate server stubs and client libraries
3. Implement business logic
4. Generate documentation automatically

## Security Considerations

### Authentication and Authorization
- Use HTTPS for all API communications
- Implement proper authentication (OAuth 2.0, JWT)
- Apply principle of least privilege
- Validate all input data
- Implement rate limiting

### Input Validation
```json
{
  "type": "object",
  "properties": {
    "email": {
      "type": "string",
      "format": "email"
    },
    "age": {
      "type": "integer",
      "minimum": 0,
      "maximum": 150
    }
  },
  "required": ["email"]
}
```

### Error Handling
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
    ],
    "timestamp": "2025-08-09T14:33:24Z",
    "requestId": "req-12345"
  }
}
```

## Performance Optimization

### Caching Strategies
- HTTP caching headers (Cache-Control, ETag)
- CDN integration for static content
- Application-level caching
- Database query optimization

### Compression
```http
GET /api/orders
Accept-Encoding: gzip, deflate

Response:
200 OK
Content-Encoding: gzip
Content-Type: application/json
```

### Connection Management
- HTTP/2 support for multiplexing
- Connection pooling
- Keep-alive connections
- Proper timeout configuration

## Monitoring and Analytics

### Key Metrics
- Request/response times
- Error rates by endpoint
- Throughput (requests per second)
- Resource utilization
- User behavior patterns

### Logging Best Practices
```json
{
  "timestamp": "2025-08-09T14:33:24Z",
  "level": "INFO",
  "method": "GET",
  "path": "/api/orders/123",
  "statusCode": 200,
  "responseTime": 45,
  "userId": "user-456",
  "correlationId": "req-789"
}
```

## Conclusion

Designing effective RESTful web APIs requires careful consideration of:

1. **Resource modeling** - Focus on business entities, not operations
2. **HTTP semantics** - Use appropriate methods and status codes
3. **URI design** - Create intuitive, hierarchical resource paths
4. **Data formats** - Support standard media types with proper content negotiation
5. **Versioning strategy** - Plan for API evolution from the beginning
6. **Performance** - Implement pagination, filtering, and caching
7. **Security** - Protect against common vulnerabilities
8. **Observability** - Enable monitoring and debugging capabilities
9. **Documentation** - Provide clear, comprehensive API documentation
10. **Standards compliance** - Follow established conventions and specifications

By following these best practices, you can create APIs that are intuitive, maintainable, scalable, and provide excellent developer experience.

## Additional Resources

- [Microsoft Azure API Guidelines](https://github.com/microsoft/api-guidelines)
- [OpenAPI Specification](https://spec.openapis.org/oas/v3.0.3)
- [RFC 7231 - HTTP/1.1 Semantics and Content](https://tools.ietf.org/html/rfc7231)
- [RFC 6902 - JSON Patch](https://tools.ietf.org/html/rfc6902)
- [RFC 7396 - JSON Merge Patch](https://tools.ietf.org/html/rfc7396)
- [Richardson Maturity Model](https://martinfowler.com/articles/richardsonMaturityModel.html)
