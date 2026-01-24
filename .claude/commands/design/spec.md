---
description: Generate comprehensive design specifications with diagrams, OpenAPI contracts, test plans, and optional spec-kit integration
allowed-tools: [Bash, Read, Write, Grep, Glob, Task, AskUserQuestion]
argument-hint: "<design-id> [--use-spec-kit] [--format <md|pdf|json|all>] [--include-spec-kit]"
---

# /design:spec - Generate Design Specifications

Generate complete design specifications from DEVB design with optional spec-kit enhancement for multi-format output, constitution compliance, and structured workflows.

## Overview

The `spec` command creates comprehensive documentation:

- **DEVB Default**: Architecture diagrams, data models, API contracts, implementation checklist
- **With Spec-Kit**: + OpenAPI 3.0, AsyncAPI 2.6, GraphQL schema, Protobuf definitions
- **With Constitution**: + Governance compliance validation, quality gates

## Execution Steps

### Step 1: Load Design Specification

Fetch the design from database:

```bash
curl -X GET http://localhost:3000/api/design/specifications/{design_id}
```

Verify design exists and has required phases:

- ✅ Design created via `/design:solution`
- ✅ Validation completed (optional but recommended)
- ✅ Ready for specification generation

If design not found:

```
❌ Design not found: {design_id}

Available designs:
1. design-abc-123: E-commerce Platform
2. design-def-456: Mobile Backend API
3. design-ghi-789: Analytics Dashboard

Create design first:
  /design:solution "Your Project Description"
```

### Step 2: Choose Specification Approach

**Ask:** "How would you like to generate the specification?"

**Option A: DEVB Standard** (Default - Fast)

- Architecture diagrams (Mermaid)
- Database ERD
- API endpoint documentation
- Implementation checklist
- Markdown + PDF export
- **Generation time**: 10-30 seconds
- **Use when**: Quick documentation needed

**Option B: Spec-Kit Enhanced** (Comprehensive)

- Everything in Standard +
- OpenAPI 3.0.3 specification
- AsyncAPI 2.6.0 (if events/async)
- GraphQL schema (if GraphQL API)
- Protocol Buffers (if gRPC)
- Constitution compliance report
- Structured workflow tracking
- **Generation time**: 60-120 seconds
- **Use when**: Need API contracts, multi-format specs, or governance validation

**Option C: Hybrid** (Recommended)

- DEVB diagrams and documentation
- Spec-kit for API contracts only (OpenAPI/AsyncAPI)
- Constitution validation
- **Generation time**: 30-60 seconds
- **Use when**: Balance between speed and completeness

### Step 3: Select Output Formats

**Ask:** "Which output formats do you need?"

**Available Formats:**

1. **Markdown** (Always included)
   - Human-readable specification
   - Includes all diagrams, tables, code blocks
   - GitHub/GitLab compatible

2. **PDF** (Optional)
   - Professional document formatting
   - Stakeholder presentations
   - Printable hardcopy

3. **JSON** (Optional)
   - Machine-readable metadata
   - CI/CD integration
   - Automated tooling

4. **OpenAPI 3.0** (Spec-Kit required)
   - Swagger UI compatible
   - API client generation
   - Contract testing

5. **AsyncAPI 2.6** (Spec-Kit required)
   - Event-driven architecture docs
   - Message broker integration
   - WebSocket/Kafka specs

6. **GraphQL SDL** (Spec-Kit required)
   - Schema definition language
   - Apollo Server compatible
   - Type generation

7. **Protobuf** (Spec-Kit required)
   - gRPC service definitions
   - Language-agnostic IDL
   - Binary serialization

8. **All Formats** (Complete package)
   - Generate everything above
   - Comprehensive artifact collection

### Step 4: Generate Specification

**For DEVB Standard:**

```bash
curl -X POST http://localhost:3000/api/design/specifications/{design_id}/generate \
  -H "Content-Type: application/json" \
  -d '{
    "format": "markdown",
    "include_diagrams": true,
    "include_api_docs": true,
    "include_checklist": true
  }'
```

**For Spec-Kit Enhanced:**

```bash
curl -X POST http://localhost:3000/api/specifications/designs/{design_id}/spec \
  -H "Content-Type: application/json" \
  -d '{
    "format": "openapi",
    "include_validation": true,
    "include_constitution_check": true
  }'
```

**For All Formats:**

```bash
curl -X POST http://localhost:3000/api/specifications/formats/generate-all \
  -H "Content-Type: application/json" \
  -d '{
    "design_id": "{design_id}",
    "include_devb": true,
    "include_spec_kit": true
  }'
```

The API will:

1. Load design specification from database
2. Generate DEVB documentation (diagrams, API docs, checklist)
3. If spec-kit enabled: Call spec-kit CLI for multi-format generation
4. If constitution linked: Validate compliance
5. Compile all artifacts into requested formats
6. Store in database and return download links

### Step 5: Display Specification Summary

Show comprehensive specification package:

```
✅ Design Specification Generated!

Design ID: {design_id}
Design Name: {design_name}
Generation Method: {devb|spec-kit|hybrid}
Generation Time: {execution_time_ms}ms

📊 SPECIFICATION PACKAGE

Total Artifacts: {artifact_count}
Total Size: {total_size_mb} MB
Export Path: {export_path}

═══════════════════════════════════════════════════════════
DEVB DOCUMENTATION
═══════════════════════════════════════════════════════════

📐 Architecture Diagrams (3)
1. System Architecture (Mermaid)
2. Database ERD (Mermaid)
3. Sequence Diagrams (Mermaid)

🗄️ Data Model
Tables: 8 defined
Relationships: 12 foreign keys
Indexes: 15 performance indexes

🔌 API Documentation
Endpoints: 23 REST endpoints
Authentication: OAuth 2.0 + JWT
Rate Limiting: 1000 req/hour per user

✅ Implementation Checklist
Tasks: 62 actionable items
Estimated: 240 hours (6 weeks)
Dependencies: Critical path identified

═══════════════════════════════════════════════════════════
SPEC-KIT SPECIFICATIONS (if enabled)
═══════════════════════════════════════════════════════════

📄 OpenAPI 3.0.3 Specification
File: openapi-spec.yaml
Size: 1,234 lines
Endpoints: 23 documented
Schemas: 15 components
Valid: ✓ Yes
Tools: Swagger UI, Postman, code generation

Preview:
```yaml
openapi: 3.0.3
info:
  title: E-commerce Platform API
  version: 1.0.0
  description: RESTful API for e-commerce operations
  contact:
    name: API Support
    email: api@example.com

servers:
  - url: https://api.example.com/v1
    description: Production server
  - url: https://staging-api.example.com/v1
    description: Staging server

paths:
  /products:
    get:
      summary: List products with pagination and filtering
      operationId: listProducts
      tags:
        - Products
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
        - name: category
          in: query
          schema:
            type: string
      responses:
        '200':
          description: Product list retrieved successfully
          content:
            application/json:
              schema:
                type: object
                properties:
                  data:
                    type: array
                    items:
                      $ref: '#/components/schemas/Product'
                  pagination:
                    $ref: '#/components/schemas/Pagination'
[... truncated ...]
```

───────────────────────────────────────────────────────────

📄 AsyncAPI 2.6.0 Specification (if event-driven)
File: asyncapi-spec.yaml
Size: 567 lines
Channels: 5 defined
Messages: 12 schemas
Protocol: Kafka / WebSocket
Valid: ✓ Yes

Preview:

```yaml
asyncapi: 2.6.0
info:
  title: E-commerce Events API
  version: 1.0.0
  description: Asynchronous event-driven architecture

servers:
  kafka:
    url: kafka.example.com:9092
    protocol: kafka
    description: Production Kafka cluster

channels:
  order.created:
    description: Channel for order creation events
    subscribe:
      operationId: onOrderCreated
      message:
        $ref: '#/components/messages/OrderCreated'

  payment.processed:
    description: Channel for payment processing events
    subscribe:
      operationId: onPaymentProcessed
      message:
        $ref: '#/components/messages/PaymentProcessed'
[... truncated ...]
```

───────────────────────────────────────────────────────────

📄 GraphQL Schema (if GraphQL API)
File: schema.graphql
Size: 890 lines
Types: 18 defined
Queries: 12 operations
Mutations: 8 operations
Subscriptions: 3 real-time
Valid: ✓ Yes

Preview:

```graphql
type Query {
  """Get product by ID"""
  product(id: ID!): Product

  """List products with filtering"""
  products(
    page: Int = 1
    limit: Int = 20
    category: String
    minPrice: Float
    maxPrice: Float
  ): ProductConnection!

  """Get current user"""
  me: User!
}

type Mutation {
  """Create new product (admin only)"""
  createProduct(input: CreateProductInput!): Product!

  """Add item to shopping cart"""
  addToCart(productId: ID!, quantity: Int!): Cart!
}

type Subscription {
  """Subscribe to order status updates"""
  orderStatusChanged(orderId: ID!): OrderStatus!
}

type Product {
  id: ID!
  name: String!
  description: String
  price: Float!
  category: Category!
  stock: Int!
  createdAt: DateTime!
}
[... truncated ...]
```

───────────────────────────────────────────────────────────

📄 Protocol Buffers (if gRPC API)
File: api.proto
Size: 456 lines
Services: 3 defined
Messages: 24 types
Valid: ✓ Yes

Preview:

```protobuf
syntax = "proto3";

package ecommerce.v1;

import "google/protobuf/timestamp.proto";

service ProductService {
  rpc ListProducts(ListProductsRequest) returns (ListProductsResponse);
  rpc GetProduct(GetProductRequest) returns (Product);
  rpc CreateProduct(CreateProductRequest) returns (Product);
  rpc UpdateProduct(UpdateProductRequest) returns (Product);
  rpc DeleteProduct(DeleteProductRequest) returns (google.protobuf.Empty);
}

message Product {
  string id = 1;
  string name = 2;
  string description = 3;
  double price = 4;
  int32 stock = 5;
  string category_id = 6;
  google.protobuf.Timestamp created_at = 7;
  google.protobuf.Timestamp updated_at = 8;
}

message ListProductsRequest {
  int32 page = 1;
  int32 limit = 2;
  string category = 3;
}
[... truncated ...]
```

═══════════════════════════════════════════════════════════
CONSTITUTION COMPLIANCE (if linked)
═══════════════════════════════════════════════════════════

Constitution: SaaS Best Practices (const-abc-123)
Compliance Score: 88/100

✓ Passed Checks (15):
  ✓ OAuth 2.0 authentication specified
  ✓ PostgreSQL as primary database
  ✓ TypeScript for backend
  ✓ Docker containerization
  ✓ OpenAPI documentation
  ✓ Rate limiting configured
  ✓ Error handling comprehensive
  ✓ Database backups specified
  ✓ HTTPS enforced
  ✓ Input validation present
  ✓ Multi-AZ deployment
  ✓ Horizontal scalability
  ✓ Monitoring configured
  ✓ CI/CD pipeline defined
  ✓ Test coverage >80%

⚠ Warnings (2):
  ⚠ Load testing not explicitly mentioned
  ⚠ Disaster recovery RPO/RTO not specified

❌ Violations (0):
  None - full compliance!

═══════════════════════════════════════════════════════════
EXPORT ARTIFACTS
═══════════════════════════════════════════════════════════

Generated Files:

📁 /workspace/{design_id}/specifications/
├── 📄 specification.md (12,345 lines)
├── 📄 specification.pdf (45 pages)
├── 📄 metadata.json (567 lines)
├── 📄 openapi-spec.yaml (1,234 lines)
├── 📄 asyncapi-spec.yaml (567 lines)
├── 📄 schema.graphql (890 lines)
├── 📄 api.proto (456 lines)
├── 📄 architecture-diagram.mermaid (89 lines)
├── 📄 database-erd.mermaid (124 lines)
├── 📄 implementation-checklist.md (620 lines)
└── 📄 constitution-compliance.md (245 lines)

Download All:
curl -X GET <http://localhost:3000/api/specifications/designs/{design_id}/export>

📁 Next Steps:
• Share with team: Send specification.pdf to stakeholders
• Generate API clients: Use OpenAPI spec with code generators
• Set up API mocking: Import OpenAPI to Postman/Prism
• Begin implementation: Follow implementation-checklist.md
• Validate specification: /spec-kit:validate {design_id}
• Generate task breakdown: /spec-kit:tasks {design_id}

```

### Step 6: Optional Actions

**Ask:** "Would you like to take any additional actions?"

**Available Actions:**

1. **Share Specification**
   - Email PDF to stakeholders
   - Upload to Confluence/Notion
   - Commit to Git repository

2. **Generate API Clients**
   - Use OpenAPI Generator for TypeScript, Python, Go
   - Create SDK for consumers

3. **Set Up API Mocking**
   - Import to Postman for mock server
   - Use Prism for local mocking
   - Enable frontend development before backend ready

4. **Validate Specification**
   - Run spec-kit validation
   - Check for ambiguities and gaps

5. **Generate Implementation Tasks**
   - Break down into actionable work items
   - Create JIRA/GitHub issues

6. **Update Design**
   - Make changes to design
   - Regenerate specification

## Advanced Features

### Use Spec-Kit for Generation
```bash
/design:spec <design-id> --use-spec-kit
```

Generate specification using spec-kit instead of DEVB.

API call:

```bash
curl -X POST http://localhost:3000/api/specifications/designs/{design_id}/spec \
  -H "Content-Type: application/json" \
  -d '{
    "format": "openapi",
    "include_validation": true
  }'
```

### Generate All Formats

```bash
/design:spec <design-id> --format all
```

Create Markdown, PDF, JSON, OpenAPI, AsyncAPI, GraphQL, and Protobuf.

### Include Spec-Kit Artifacts

```bash
/design:spec <design-id> --include-spec-kit
```

Add spec-kit structured workflow artifacts (clarify, analyze, plan, tasks).

### Export to Specific Path

```bash
/design:spec <design-id> --export ./docs/specifications/
```

Export all artifacts to custom directory.

### Regenerate Specification

```bash
/design:spec <design-id> --regenerate
```

Rebuild specification from latest design changes.

### OpenAPI Code Generation Examples

**TypeScript Client:**

```bash
npx @openapitools/openapi-generator-cli generate \
  -i openapi-spec.yaml \
  -g typescript-axios \
  -o ./src/generated/api-client
```

**Python Client:**

```bash
openapi-generator generate \
  -i openapi-spec.yaml \
  -g python \
  -o ./python-client
```

**Go Client:**

```bash
openapi-generator generate \
  -i openapi-spec.yaml \
  -g go \
  -o ./go-client
```

### API Mocking with Prism

```bash
# Install Prism
npm install -g @stoplight/prism-cli

# Start mock server
prism mock openapi-spec.yaml --port 4010

# Test mock API
curl http://localhost:4010/products
```

## Error Handling

**If design not found:**

```
❌ Design not found: {design_id}

Available designs:
1. design-abc-123: E-commerce Platform
2. design-def-456: Mobile Backend

Create design first:
  /design:solution "Your Description"
```

**If spec generation fails:**

```
❌ Specification generation failed: {error_message}

Common causes:
1. Design incomplete or missing required sections
2. spec-kit CLI not available (if using --use-spec-kit)
3. Invalid design data (malformed JSON)

Try:
1. Validate design: /design:validate {design_id}
2. Check spec-kit health: curl http://localhost:3000/api/spec-kit/health
3. Regenerate design: /design:solution {description}
```

**If format not supported:**

```
⚠️ Format not available: {format}

Without --use-spec-kit flag:
  ✓ Available: markdown, pdf, json
  ✗ Unavailable: openapi, asyncapi, graphql, protobuf

Enable spec-kit for multi-format support:
  /design:spec {design_id} --use-spec-kit --format all
```

## Example Usage

### Example 1: Quick Documentation

```
User: /design:spec design-abc-123
Assistant: Generating DEVB specification...
  Architecture diagram: ✓
  Database ERD: ✓
  API documentation: ✓
  Checklist: ✓
Assistant: ✅ Specification generated!
  Format: Markdown (12,345 lines)
  Export: /workspace/design-abc-123/specification.md
```

### Example 2: Full API Contracts

```
User: /design:spec design-def-456 --use-spec-kit --format all
Assistant: Generating comprehensive specification package...
  DEVB documentation: ✓
  OpenAPI 3.0: ✓ (1,234 lines)
  AsyncAPI 2.6: ✓ (567 lines)
  GraphQL schema: ✓ (890 lines)
  Protobuf: ✓ (456 lines)
  Constitution check: ✓ (88/100)
Assistant: ✅ All formats generated!
  Total: 8 artifacts, 45 MB
```

### Example 3: Hybrid Approach

```
User: /design:spec design-ghi-789 --include-spec-kit
Assistant: Using hybrid generation (DEVB + spec-kit)...
  DEVB diagrams: ✓
  OpenAPI for REST API: ✓
  Constitution validation: ✓
Assistant: ✅ Specification complete!
  Best of both: Speed + API contracts
```

## Success Criteria

✅ Specification generated with all requested formats
✅ Artifacts stored in database and workspace
✅ Download links provided
✅ Constitution compliance checked (if applicable)
✅ User ready for implementation or next steps

## Notes

- DEVB default is fastest (10-30s)
- Spec-kit adds 30-90s but provides API contracts
- Hybrid is recommended for most projects
- All artifacts versioned in database
- Specifications can be regenerated anytime
- Use OpenAPI for automatic API client generation
- Use AsyncAPI for event-driven architectures
- Constitution compliance automatic if design linked
- PDF format ideal for stakeholder presentations

## Integration with Workflow

```
Design → Emulate → Validate → **Spec** → Implement
                                 ↓
                        Share with team,
                        Generate clients,
                        Set up mocking
```

Specification is the final deliverable before implementation begins. It serves as the contract between design and development.
