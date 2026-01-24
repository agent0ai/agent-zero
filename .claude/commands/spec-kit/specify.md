---
description: Generate detailed specifications with user stories, API contracts, and multi-format output
allowed-tools: [Bash, Read, Write, AskUserQuestion]
argument-hint: "<design-id> [--format <openapi|asyncapi|graphql|protobuf>] [--validate]"
---

# /spec-kit:specify - Generate Detailed Specifications

Generate comprehensive specifications from design requirements with user stories, functional requirements, and multi-format API contracts.

## Overview

The `specify` command transforms high-level requirements into detailed specifications:

- **User Stories**: As a / I want / So that format
- **Functional Requirements**: Detailed feature specifications
- **Non-Functional Requirements**: Performance, security, scalability
- **API Contracts**: OpenAPI, AsyncAPI, GraphQL, or Protobuf
- **Validation**: Automatic compliance checking

## Execution Steps

### Step 1: Identify Design or Create New

**Ask:** "Do you want to specify an existing design or create a new one?"

**Option A: Existing Design**

- Ask for design ID
- Fetch design from database
- Load existing requirements

**Option B: New Design**

- Create design first using `/design:solution`
- Then run specify on the new design

### Step 2: Load Design and Workflow

Fetch the design specification:

```bash
curl -X GET http://localhost:3000/api/design/specifications/{design_id}
```

Check if spec-kit workflow exists:

```bash
curl -X GET http://localhost:3000/api/specifications/designs/{design_id}/workflow
```

If no workflow exists, ask: "Would you like to start with a constitution?" (Yes/No)

If Yes:

- Run `/spec-kit:constitution` first
- Create design with constitution
- Initialize workflow

If No:

- Initialize workflow without constitution

### Step 3: Gather Requirements (Interactive Mode)

**3.1 Problem Definition**
Ask: "What problem does this solve?" (1-2 sentences)

**3.2 User Stories** (3-10 stories)
Ask: "Let's create user stories. How many user stories do you need?" (3-10)

For each user story, collect in format:

```
As a [user type]
I want [functionality]
So that [benefit]
```

Example:

```
As a customer
I want to search for products by category
So that I can find items I'm interested in quickly
```

**3.3 Functional Requirements**
Ask: "What are the functional requirements?" (API endpoints, features, data models)

Collect:

- API endpoints needed (e.g., GET /products, POST /orders)
- Data models (e.g., User, Product, Order)
- Business rules (e.g., "Orders over $100 get free shipping")
- Integration points (e.g., "Integrate with Stripe for payments")

**3.4 Non-Functional Requirements**
Ask: "What are the non-functional requirements?"

Collect:

- Performance targets (e.g., "API response time <500ms")
- Scalability needs (e.g., "Support 10,000 concurrent users")
- Security requirements (e.g., "OAuth 2.0 authentication")
- Availability targets (e.g., "99.9% uptime")
- Compliance needs (e.g., "GDPR compliant")

**3.5 Choose Output Format**
Ask: "Which specification format would you like?" (can choose multiple)

Options:

1. **OpenAPI 3.0** - RESTful APIs with Swagger documentation
2. **AsyncAPI 2.6** - Event-driven/async messaging APIs
3. **GraphQL** - GraphQL schema with queries and mutations
4. **Protobuf** - Protocol Buffer definitions for gRPC
5. **All formats** - Generate all four formats

### Step 4: Generate Specification via API

Call the specifications API:

```bash
curl -X POST http://localhost:3000/api/specifications/designs/{design_id}/spec \
  -H "Content-Type: application/json" \
  -d '{
    "format": "{selected_format}",
    "include_validation": true
  }'
```

The API will:

1. Build specification input from design requirements
2. Call spec-kit CLI to generate specification
3. Store artifacts in database
4. Advance workflow to 'plan' phase
5. Run validation if requested
6. Return specification with artifacts

### Step 5: Display Specification Summary

Show a comprehensive summary:

```
✅ Specification Generated Successfully!

Design ID: {design_id}
Workflow ID: {workflow_id}
Current Phase: Specify → Plan
Progress: 60%

📋 Specification Details:

User Stories ({count}):
1. As a customer, I want to browse products, so that I can find items I like
2. As a customer, I want to add items to cart, so that I can purchase multiple items
3. As a customer, I want to checkout securely, so that my payment is safe
[... more stories ...]

Functional Requirements ({count}):
✓ Product catalog with search and filtering
✓ Shopping cart with session persistence
✓ Secure checkout with Stripe integration
✓ Order tracking and history
✓ User authentication and profiles

Non-Functional Requirements ({count}):
✓ Performance: API response <500ms (p95)
✓ Scalability: 10,000 concurrent users
✓ Security: OAuth 2.0 + JWT tokens
✓ Availability: 99.9% uptime SLA
✓ Compliance: PCI DSS for payment data

📄 Generated Formats:

{format_type} Specification:
• File: {artifact_filename}
• Size: {size_kb} KB
• Valid: ✓ Yes
• Endpoints: {endpoint_count}
• Schemas: {schema_count}

Validation Results:
✓ All required fields present
✓ No conflicts detected
⚠ 2 warnings:
  - Consider adding rate limiting
  - Add pagination to list endpoints

Preview:
```yaml
openapi: 3.0.3
info:
  title: E-commerce API
  version: 1.0.0
  description: RESTful API for e-commerce platform

servers:
  - url: https://api.example.com/v1
    description: Production server

paths:
  /products:
    get:
      summary: List products
      parameters:
        - name: category
          in: query
          schema:
            type: string
      responses:
        '200':
          description: Product list
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/Product'
[... truncated ...]
```

📊 Artifacts Generated:

1. specification.yaml (OpenAPI 3.0) - 1,234 lines
2. user-stories.md - 45 stories
3. requirements.md - Functional + Non-functional
4. data-model.md - Entity relationship diagram

💾 Storage:
All artifacts stored in database and workspace:
{workspace_path}

📁 Next Steps:
• Generate implementation plan: /spec-kit:plan {design_id}
• Validate specification: /spec-kit:validate {design_id} --mode analyze
• Export specification: /spec-kit:specify {design_id} --export ./specs/
• Generate all formats: /spec-kit:specify {design_id} --all-formats

```

### Step 6: Optional Actions

Ask if the user wants to:
- **Generate implementation plan** - Move to plan phase
- **Run validation** - Clarify or analyze the specification
- **Export to file** - Save specification artifacts
- **Generate additional formats** - Create other spec formats
- **Link to constitution** - Validate against governance

## Advanced Features

### Generate All Formats
```bash
/spec-kit:specify <design-id> --all-formats
```

Generates OpenAPI, AsyncAPI, GraphQL, and Protobuf simultaneously.

API call:

```bash
curl -X POST http://localhost:3000/api/specifications/formats/generate-all \
  -H "Content-Type: application/json" \
  -d '{"design_id": "{design_id}"}'
```

### Validate Specification

```bash
/spec-kit:specify <design-id> --validate
```

Runs validation to find:

- Underspecified requirements (clarify mode)
- Inconsistencies (analyze mode)
- Missing elements

### Export to File

```bash
/spec-kit:specify <design-id> --export <path>
```

Exports all specification artifacts to directory.

API call:

```bash
curl -X POST http://localhost:3000/api/specifications/formats/export \
  -H "Content-Type: application/json" \
  -d '{
    "specification": {spec_object},
    "format": "openapi",
    "export_path": "{path}/specification.yaml"
  }'
```

### View Workflow Status

```bash
/spec-kit:specify <design-id> --status
```

Shows current workflow phase and completion percentage.

API call:

```bash
curl -X GET http://localhost:3000/api/specifications/designs/{design_id}/workflow
```

## Constitution Compliance

If design has linked constitution:

1. Automatically validate specification against constitution
2. Check for constraint violations
3. Verify preferred stack usage
4. Report compliance score (0-100)

Display compliance results:

```
🔒 Constitution Compliance Check

Constitution: SaaS Best Practices (const-abc-123)
Compliance Score: 85/100

✓ Passed Checks (12):
  ✓ All APIs use authentication (OAuth 2.0)
  ✓ Rate limiting specified (1000 req/hour)
  ✓ Error handling follows standard format
  ✓ All endpoints documented in OpenAPI
  [... more ...]

⚠ Warnings (3):
  ⚠ Multi-tenancy isolation not explicitly mentioned
  ⚠ Scalability target below recommended (10k vs 50k users)
  ⚠ Using MySQL instead of preferred PostgreSQL

❌ Violations (1):
  ❌ No encryption specified for data at rest

Recommendations:
1. Add explicit tenant isolation mechanism
2. Consider increasing scalability target
3. Implement data encryption (AES-256)
4. Evaluate PostgreSQL for better JSON support
```

## Multi-Format Output

### OpenAPI 3.0 (REST APIs)

- Full Swagger documentation
- Request/response schemas
- Authentication schemes
- Examples and descriptions

### AsyncAPI 2.6 (Event-driven)

- Pub/sub channels
- Message schemas
- Event flows
- WebSocket/Kafka/RabbitMQ support

### GraphQL

- Schema definition language (SDL)
- Queries, Mutations, Subscriptions
- Type definitions
- Resolvers outline

### Protobuf

- .proto file definitions
- Service definitions
- Message types
- gRPC service contracts

## Error Handling

**If design not found:**

```
❌ Design not found: {design_id}

Available designs:
1. design-abc-123: E-commerce Platform
2. design-def-456: Mobile App Backend
3. design-ghi-789: Analytics Dashboard

Try: /spec-kit:specify <design-id>
Or create new design: /design:solution "New Project"
```

**If workflow not initialized:**

```
⚠️ No spec-kit workflow found for this design.

Would you like to:
1. Start with constitution (recommended)
2. Start without constitution

[User selects option]
```

**If validation fails:**

```
⚠️ Specification validation found issues:

Errors (2):
1. Missing required field: info.title
2. Invalid OpenAPI version: must be 3.x

Warnings (1):
1. No paths defined in specification

Fix these issues and try again, or continue anyway? (fix/continue)
```

## Example Usage

### Example 1: E-commerce API

```
User: /spec-kit:specify design-abc-123 --format openapi
Assistant: Generating OpenAPI specification...
  User stories: 8 collected
  Functional requirements: 12 defined
  API endpoints: 15 designed
Assistant: ✅ OpenAPI specification generated!
  Preview: GET /products, POST /orders, GET /users/{id}
  Validation: Passed with 2 warnings
```

### Example 2: Event-Driven System

```
User: /spec-kit:specify design-def-456 --format asyncapi
Assistant: Generating AsyncAPI specification...
  Events: order.created, payment.processed, shipment.tracking
  Channels: orders, payments, shipments
Assistant: ✅ AsyncAPI 2.6 specification generated!
  Broker: Kafka
  Channels: 3 defined
  Messages: 8 schemas
```

### Example 3: All Formats

```
User: /spec-kit:specify design-ghi-789 --all-formats
Assistant: Generating all specification formats...
  OpenAPI: ✓ Generated (1,234 lines)
  AsyncAPI: ✓ Generated (567 lines)
  GraphQL: ✓ Generated (890 lines)
  Protobuf: ✓ Generated (456 lines)
Assistant: ✅ All formats generated successfully!
```

## Success Criteria

✅ Specification generated with all required elements
✅ Format validation passed (or warnings acknowledged)
✅ Artifacts stored in database
✅ Workflow advanced to plan phase
✅ User knows next steps

## Notes

- Specifications can be regenerated with different formats
- Validation is recommended but optional
- Constitution compliance is automatic if linked
- All artifacts are versioned in the database
- Workspace files are preserved for 24 hours
- Use `/spec-kit:validate` for deeper analysis
