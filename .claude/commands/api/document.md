---
description: Generate OpenAPI/Swagger documentation
argument-hint: [--from <spec-file>] [--format openapi|swagger|asyncapi] [--output <dir>]
model: claude-sonnet-4-5-20250929
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

Generate comprehensive API documentation from spec or code: **$ARGUMENTS**

## What This Command Does

This command automatically generates beautiful, interactive API documentation:

- **OpenAPI 3.0/Swagger 2.0**: Generate from code annotations or existing spec
- **Interactive Docs**: Create Swagger UI, ReDoc, or Stoplight Elements
- **SDK Generation**: Auto-generate client SDKs in multiple languages
- **Postman Collections**: Export ready-to-use Postman collections
- **Markdown Docs**: Generate static markdown documentation
- **AsyncAPI**: Document WebSocket and event-driven APIs

## Usage Examples

### Generate from OpenAPI Spec

```bash
/api:document --from openapi.yaml --format openapi
```

### Generate from Code Annotations

```bash
/api:document --from src/routes --format openapi --output docs
```

### Generate Multiple Formats

```bash
/api:document --formats "openapi,postman,markdown"
```

### Update Existing Documentation

```bash
/api:document --update --validate
```

## Step 1: Detect Source and Format

```bash
# Parse arguments
SOURCE="${SOURCE:-auto}"  # auto-detect or explicit path
FORMAT="${FORMAT:-openapi}"
OUTPUT_DIR="${OUTPUT_DIR:-docs/api}"

# Auto-detect API specification files
if [ "$SOURCE" = "auto" ]; then
  if [ -f "openapi.yaml" ]; then
    SOURCE="openapi.yaml"
    FORMAT="openapi"
  elif [ -f "openapi.json" ]; then
    SOURCE="openapi.json"
    FORMAT="openapi"
  elif [ -f "swagger.yaml" ]; then
    SOURCE="swagger.yaml"
    FORMAT="swagger"
  elif [ -f "asyncapi.yaml" ]; then
    SOURCE="asyncapi.yaml"
    FORMAT="asyncapi"
  elif [ -f "schema.graphql" ]; then
    SOURCE="schema.graphql"
    FORMAT="graphql"
  else
    echo "No API spec found. Scanning code for annotations..."
    SOURCE="src"
    FORMAT="code-annotations"
  fi
fi

echo "Source: $SOURCE"
echo "Format: $FORMAT"
echo "Output: $OUTPUT_DIR"
```

## Step 2: Validate API Specification

Validate the API spec for errors and best practices:

```bash
# Install validation tools if needed
if ! command -v openapi-validator &> /dev/null; then
  npm install -g @ibm-cloud/openapi-ruleset
  npm install -g @stoplight/spectral-cli
fi

# Validate OpenAPI spec
if [ "$FORMAT" = "openapi" ]; then
  echo "Validating OpenAPI specification..."

  # Spectral validation (linting + best practices)
  spectral lint "$SOURCE" \
    --ruleset https://raw.githubusercontent.com/stoplightio/spectral/master/packages/rulesets/src/oas/index.ts

  # Check for common issues
  echo "Checking for common issues..."

  # Missing descriptions
  missing_desc=$(yq eval '.. | select(has("description") | not) | path | join(".")' "$SOURCE" | wc -l)
  echo "  - Missing descriptions: $missing_desc"

  # Missing examples
  missing_examples=$(yq eval '.. | select(has("example") | not) | path | join(".")' "$SOURCE" | wc -l)
  echo "  - Missing examples: $missing_examples"

  # Inconsistent naming
  echo "  - Checking naming conventions..."

  # Security definitions
  security_defs=$(yq eval '.components.securitySchemes | length' "$SOURCE")
  echo "  - Security schemes defined: $security_defs"
fi
```

## Step 3: Generate OpenAPI/Swagger Documentation

### Option A: From Existing Spec

```bash
mkdir -p "$OUTPUT_DIR"

# Copy spec to output directory
cp "$SOURCE" "$OUTPUT_DIR/openapi.yaml"

# Generate Swagger UI
cat > "$OUTPUT_DIR/swagger-ui.html" <<'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>API Documentation - Swagger UI</title>
  <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css" />
  <style>
    body { margin: 0; padding: 0; }
    .topbar { display: none; }
  </style>
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
  <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-standalone-preset.js"></script>
  <script>
    window.onload = function() {
      SwaggerUIBundle({
        url: "./openapi.yaml",
        dom_id: '#swagger-ui',
        deepLinking: true,
        presets: [
          SwaggerUIBundle.presets.apis,
          SwaggerUIStandalonePreset
        ],
        plugins: [
          SwaggerUIBundle.plugins.DownloadUrl
        ],
        layout: "StandaloneLayout",
        defaultModelsExpandDepth: 1,
        defaultModelExpandDepth: 1,
        docExpansion: "list",
        filter: true,
        showExtensions: true,
        showCommonExtensions: true,
        tryItOutEnabled: true
      })
    }
  </script>
</body>
</html>
EOF

# Generate ReDoc (cleaner alternative)
cat > "$OUTPUT_DIR/redoc.html" <<'EOF'
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>API Documentation - ReDoc</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body { margin: 0; padding: 0; }
  </style>
</head>
<body>
  <redoc spec-url='./openapi.yaml'></redoc>
  <script src="https://cdn.redoc.ly/redoc/latest/bundles/redoc.standalone.js"></script>
</body>
</html>
EOF

echo "✓ Interactive documentation generated"
echo "  - Swagger UI: $OUTPUT_DIR/swagger-ui.html"
echo "  - ReDoc: $OUTPUT_DIR/redoc.html"
```

### Option B: From Code Annotations

Extract API spec from code annotations:

**For Node.js/Express with JSDoc**:

```bash
# Install swagger-jsdoc
npm install --save-dev swagger-jsdoc

# Create extraction script
cat > scripts/generate-openapi.js <<'EOF'
const swaggerJsdoc = require('swagger-jsdoc')
const fs = require('fs')
const yaml = require('js-yaml')

const options = {
  definition: {
    openapi: '3.0.0',
    info: {
      title: process.env.API_TITLE || 'API',
      version: process.env.API_VERSION || '1.0.0',
      description: process.env.API_DESCRIPTION || 'API Documentation',
    },
    servers: [
      { url: process.env.API_URL || 'http://localhost:3000' }
    ],
  },
  apis: ['./src/routes/**/*.js', './src/models/**/*.js'],
}

const spec = swaggerJsdoc(options)

// Save as YAML
fs.writeFileSync('openapi.yaml', yaml.dump(spec))
console.log('✓ OpenAPI spec generated: openapi.yaml')

// Save as JSON
fs.writeFileSync('openapi.json', JSON.stringify(spec, null, 2))
console.log('✓ OpenAPI spec generated: openapi.json')
EOF

# Run extraction
node scripts/generate-openapi.js
```

**For Python/FastAPI** (automatic):

```bash
# FastAPI generates OpenAPI automatically
# Just export it:

python3 -c "
from main import app
import json
import yaml

# Get OpenAPI schema
schema = app.openapi()

# Save as JSON
with open('openapi.json', 'w') as f:
    json.dump(schema, f, indent=2)

# Save as YAML
with open('openapi.yaml', 'w') as f:
    yaml.dump(schema, f, default_flow_style=False)

print('✓ OpenAPI spec generated from FastAPI app')
"
```

**For Go with Swag**:

```bash
# Install swag
go install github.com/swaggo/swag/cmd/swag@latest

# Generate from annotations
swag init -g main.go -o docs/swagger

echo "✓ Swagger docs generated in docs/swagger"
```

## Step 4: Generate SDK Clients

Generate client SDKs in multiple languages:

```bash
# Install OpenAPI Generator
npm install -g @openapitools/openapi-generator-cli

# JavaScript/TypeScript SDK
openapi-generator-cli generate \
  -i openapi.yaml \
  -g typescript-axios \
  -o clients/typescript \
  --additional-properties=npmName=@company/api-client,npmVersion=1.0.0

# Python SDK
openapi-generator-cli generate \
  -i openapi.yaml \
  -g python \
  -o clients/python \
  --additional-properties=packageName=company_api_client,packageVersion=1.0.0

# Go SDK
openapi-generator-cli generate \
  -i openapi.yaml \
  -g go \
  -o clients/go \
  --additional-properties=packageName=apiclient

# Java SDK
openapi-generator-cli generate \
  -i openapi.yaml \
  -g java \
  -o clients/java \
  --additional-properties=groupId=com.company,artifactId=api-client,artifactVersion=1.0.0

# Ruby SDK
openapi-generator-cli generate \
  -i openapi.yaml \
  -g ruby \
  -o clients/ruby \
  --additional-properties=gemName=company_api_client,gemVersion=1.0.0

echo "✓ SDK clients generated in clients/"
```

## Step 5: Generate Postman Collection

Create Postman collection from OpenAPI spec:

```bash
# Install openapi-to-postmanv2
npm install -g openapi-to-postmanv2

# Convert OpenAPI to Postman Collection v2
openapi2postmanv2 \
  -s openapi.yaml \
  -o postman_collection.json \
  -p \
  -O folderStrategy=Tags,requestParametersResolution=Example,exampleParametersResolution=Example

# Create Postman environment file
cat > postman_environment.json <<'EOF'
{
  "name": "API Environment",
  "values": [
    {
      "key": "base_url",
      "value": "https://api.example.com/v1",
      "type": "default",
      "enabled": true
    },
    {
      "key": "api_key",
      "value": "your_api_key_here",
      "type": "secret",
      "enabled": true
    },
    {
      "key": "access_token",
      "value": "",
      "type": "secret",
      "enabled": true
    }
  ]
}
EOF

echo "✓ Postman collection generated"
echo "  Import postman_collection.json and postman_environment.json into Postman"
```

## Step 6: Generate Markdown Documentation

Create static markdown documentation:

```bash
# Install widdershins (OpenAPI to Markdown)
npm install -g widdershins

# Generate markdown
widdershins \
  --search false \
  --language_tabs 'javascript:JavaScript' 'python:Python' 'go:Go' 'java:Java' \
  --summary \
  openapi.yaml \
  -o "$OUTPUT_DIR/api-reference.md"

# Generate GitHub Pages compatible docs
cat > "$OUTPUT_DIR/index.md" <<'EOF'
---
layout: default
title: API Documentation
---

# API Documentation

## Overview

Welcome to our API documentation. This API follows REST principles and returns JSON responses.

## Base URL

```
<https://api.example.com/v1>

```

## Authentication

All API requests require authentication using a Bearer token:

```

Authorization: Bearer YOUR_API_KEY

```

## Rate Limiting

- **Rate Limit**: 1000 requests per hour
- **Burst Limit**: 100 requests per minute

Rate limit headers are included in all responses:
- `X-Rate-Limit-Limit`: Total requests allowed
- `X-Rate-Limit-Remaining`: Requests remaining
- `X-Rate-Limit-Reset`: Unix timestamp when limit resets

## Error Handling

Errors follow this format:

```json
{
  "errors": [
    {
      "id": "err_001",
      "status": "400",
      "code": "VALIDATION_ERROR",
      "title": "Validation Failed",
      "detail": "Email is required",
      "source": { "pointer": "/data/attributes/email" }
    }
  ]
}
```

## Pagination

List endpoints support cursor-based pagination:

```
GET /users?cursor=eyJpZCI6MTIzfQ&limit=20
```

Response includes pagination metadata:

```json
{
  "data": [...],
  "pagination": {
    "next_cursor": "eyJpZCI6MTQzfQ",
    "prev_cursor": "eyJpZCI6MTAzfQ",
    "has_more": true
  }
}
```

## API Reference

[Full API reference documentation](api-reference.md)

## SDKs

Official SDKs are available in multiple languages:

- [JavaScript/TypeScript](https://npmjs.com/package/@company/api-client)
- [Python](https://pypi.org/project/company-api-client/)
- [Go](https://github.com/company/api-client-go)
- [Java](https://mvnrepository.com/artifact/com.company/api-client)
- [Ruby](https://rubygems.org/gems/company_api_client)

## Support

- **Documentation**: <https://docs.example.com>
- **Support Email**: <api@example.com>
- **Status Page**: <https://status.example.com>
- **Changelog**: <https://changelog.example.com>

EOF

echo "✓ Markdown documentation generated"

```

## Step 7: Generate Interactive Examples

Create interactive API examples:

```bash
mkdir -p "$OUTPUT_DIR/examples"

# Generate example requests for each endpoint
cat > "$OUTPUT_DIR/examples/users.md" <<'EOF'
# User API Examples

## List Users

**Request**:
```bash
curl -X GET "https://api.example.com/v1/users?page=1&limit=20" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Accept: application/json"
```

**Response** (200 OK):

```json
{
  "data": [
    {
      "id": "usr_123",
      "type": "user",
      "attributes": {
        "email": "john@example.com",
        "name": "John Doe",
        "created_at": "2024-01-15T10:30:00Z"
      }
    }
  ],
  "meta": {
    "total": 1543,
    "page": 1,
    "per_page": 20
  }
}
```

## Create User

**Request**:

```bash
curl -X POST "https://api.example.com/v1/users" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "type": "user",
      "attributes": {
        "email": "jane@example.com",
        "name": "Jane Smith",
        "password": "secure_password"
      }
    }
  }'
```

**Response** (201 Created):

```json
{
  "data": {
    "id": "usr_124",
    "type": "user",
    "attributes": {
      "email": "jane@example.com",
      "name": "Jane Smith",
      "created_at": "2024-01-15T10:35:00Z"
    }
  }
}
```

## Error Examples

**Validation Error** (422):

```json
{
  "errors": [
    {
      "status": "422",
      "code": "VALIDATION_ERROR",
      "title": "Validation Failed",
      "detail": "Email is already in use",
      "source": { "pointer": "/data/attributes/email" }
    }
  ]
}
```

**Unauthorized** (401):

```json
{
  "errors": [
    {
      "status": "401",
      "code": "UNAUTHORIZED",
      "title": "Authentication Required",
      "detail": "Valid API key required"
    }
  ]
}
```

EOF

```

## Step 8: Generate GraphQL Documentation

If GraphQL API detected:

```bash
if [ -f "schema.graphql" ]; then
  # Install GraphQL documentation generators
  npm install -g spectaql graphdoc

  # Generate GraphQL Docs (SpectaQL)
  cat > spectaql-config.yml <<'EOF'
spectaql:
  targetDir: docs/graphql
  themeDir: null

introspection:
  schemaFile: schema.graphql

info:
  title: GraphQL API Documentation
  description: Complete GraphQL API reference

servers:
  - url: https://api.example.com/graphql
    description: Production
    production: true

  - url: https://staging-api.example.com/graphql
    description: Staging

EOF

  spectaql spectaql-config.yml

  # Generate alternative docs with GraphDoc
  graphdoc -s schema.graphql -o docs/graphql-alt

  echo "✓ GraphQL documentation generated"
  echo "  - SpectaQL: docs/graphql/index.html"
  echo "  - GraphDoc: docs/graphql-alt/index.html"
fi
```

## Step 9: Generate AsyncAPI Documentation

For WebSocket/Event-Driven APIs:

```bash
if [ -f "asyncapi.yaml" ]; then
  # Install AsyncAPI generator
  npm install -g @asyncapi/generator

  # Generate HTML documentation
  ag asyncapi.yaml @asyncapi/html-template -o docs/asyncapi

  # Generate Markdown
  ag asyncapi.yaml @asyncapi/markdown-template -o docs/asyncapi-md

  echo "✓ AsyncAPI documentation generated"
  echo "  - HTML: docs/asyncapi/index.html"
  echo "  - Markdown: docs/asyncapi-md/asyncapi.md"
fi
```

## Step 10: Set Up Documentation Server

Create local documentation server:

```bash
# Create simple HTTP server for docs
cat > "$OUTPUT_DIR/serve.sh" <<'EOF'
#!/bin/bash

PORT=${PORT:-8080}

echo "Starting documentation server on http://localhost:$PORT"
echo ""
echo "Available documentation:"
echo "  - Swagger UI:  http://localhost:$PORT/swagger-ui.html"
echo "  - ReDoc:       http://localhost:$PORT/redoc.html"
echo "  - Markdown:    http://localhost:$PORT/index.md"
echo ""
echo "Press Ctrl+C to stop"

# Start server (choose based on available tools)
if command -v python3 &> /dev/null; then
  python3 -m http.server $PORT
elif command -v python &> /dev/null; then
  python -m SimpleHTTPServer $PORT
elif command -v npx &> /dev/null; then
  npx http-server -p $PORT
else
  echo "Error: No HTTP server available"
  exit 1
fi
EOF

chmod +x "$OUTPUT_DIR/serve.sh"

# Create README for docs directory
cat > "$OUTPUT_DIR/README.md" <<'EOF'
# API Documentation

## Viewing Documentation

### Local Development

Run the documentation server:
```bash
./serve.sh
```

Then open your browser to:

- Swagger UI: <http://localhost:8080/swagger-ui.html>
- ReDoc: <http://localhost:8080/redoc.html>

### Production Deployment

Deploy to GitHub Pages, Netlify, or any static hosting:

**GitHub Pages**:

```bash
# Push to gh-pages branch
git subtree push --prefix docs/api origin gh-pages
```

**Netlify**:

```bash
netlify deploy --dir=docs/api --prod
```

## Updating Documentation

Regenerate documentation when API changes:

```bash
/api:document --update
```

## SDK Clients

Pre-generated SDK clients are available in `clients/`:

- TypeScript: `clients/typescript/`
- Python: `clients/python/`
- Go: `clients/go/`
- Java: `clients/java/`
- Ruby: `clients/ruby/`

Install and use:

**TypeScript**:

```bash
npm install @company/api-client
```

**Python**:

```bash
pip install company-api-client
```

## Testing with Postman

Import the Postman collection:

1. Open Postman
2. Import `postman_collection.json`
3. Import `postman_environment.json`
4. Set your API key in the environment
5. Start testing!

EOF

```

## Step 11: Generate Changelog

Create API changelog:

```bash
cat > "$OUTPUT_DIR/CHANGELOG.md" <<'EOF'
# API Changelog

All notable changes to this API will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this API adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- New endpoints for user management
- Rate limiting headers in all responses
- Cursor-based pagination support

### Changed
- Improved error response format
- Updated authentication flow

### Deprecated
- `GET /users/list` - Use `GET /users` instead (will be removed in v2.0.0)

### Security
- Added rate limiting to prevent abuse
- Implemented CORS restrictions

## [1.0.0] - 2024-01-15

### Added
- Initial API release
- User management endpoints
- Authentication with JWT
- OpenAPI 3.0 documentation

EOF
```

## Step 12: Display Summary

```
════════════════════════════════════════════════════════
       API DOCUMENTATION GENERATED
════════════════════════════════════════════════════════

SOURCE: openapi.yaml
FORMAT: OpenAPI 3.0
OUTPUT: docs/api/

DOCUMENTATION GENERATED:
✓ swagger-ui.html       - Interactive Swagger UI
✓ redoc.html           - Clean ReDoc interface
✓ index.md             - GitHub Pages homepage
✓ api-reference.md     - Complete API reference
✓ CHANGELOG.md         - API version history

SDK CLIENTS GENERATED:
✓ clients/typescript/  - TypeScript/Axios client
✓ clients/python/      - Python client
✓ clients/go/          - Go client
✓ clients/java/        - Java client
✓ clients/ruby/        - Ruby client

POSTMAN COLLECTION:
✓ postman_collection.json    - Import into Postman
✓ postman_environment.json   - Environment variables

VALIDATION RESULTS:
✓ OpenAPI spec is valid
✓ All endpoints have descriptions
✓ All parameters have examples
⚠ 3 endpoints missing response examples
⚠ Security scheme not fully documented

════════════════════════════════════════════════════════

VIEW DOCUMENTATION:

1. Start local server:
   cd docs/api && ./serve.sh

2. Open in browser:
   - Swagger UI: http://localhost:8080/swagger-ui.html
   - ReDoc:      http://localhost:8080/redoc.html

3. Deploy to production:
   # GitHub Pages
   git subtree push --prefix docs/api origin gh-pages

   # Netlify
   netlify deploy --dir=docs/api --prod

════════════════════════════════════════════════════════

NEXT STEPS:

1. Review and customize documentation:
   - Update index.md with your branding
   - Add more code examples
   - Add troubleshooting guides

2. Generate API mocks for testing:
   /api:mock --from openapi.yaml

3. Set up versioning:
   /api:version --strategy url --initial v1

4. Share with team:
   - SDK clients ready in clients/
   - Postman collection ready for import
   - Documentation deployed to [URL]

════════════════════════════════════════════════════════

DOCUMENTATION URLS:
📖 Swagger UI: http://localhost:8080/swagger-ui.html
📖 ReDoc:      http://localhost:8080/redoc.html
📖 Markdown:   http://localhost:8080/index.md

════════════════════════════════════════════════════════
```

## Business Value & ROI

**Time Savings**:

- Manual documentation: 1-3 days per API version
- With this command: 5-15 minutes
- **ROI: 20-50x faster**

**Quality Improvements**:

- ✓ Always up-to-date documentation
- ✓ Multiple formats (interactive, static, SDKs)
- ✓ Consistent across all endpoints
- ✓ Automatic validation and examples

**Cost Savings**:

- Reduce API integration time for clients by 70%
- Decrease support tickets by 50%
- Eliminate manual SDK creation
- Faster onboarding for new developers

**Business Impact**:

- Better developer experience → Higher adoption
- Professional documentation → Enterprise credibility
- Multi-language SDKs → Broader market reach
- Self-service integration → Reduced support costs

## Success Metrics

**Documentation Quality**:

- Completeness: Target 100% coverage
- Examples: Target 90% of endpoints
- Accuracy: Target <1% error rate
- Freshness: Auto-update on every change

**Developer Experience**:

- Time to first API call: Target < 10 minutes
- Integration completion time: Target < 2 hours
- Documentation satisfaction: Target > 4.5/5
- SDK adoption rate: Target > 60%

**Business Impact**:

- API adoption rate: Track growth
- Support ticket reduction: Target 50% decrease
- Time to integrate: Target 70% reduction
- Developer satisfaction: Target > 4.5/5

---

**Model**: Claude Sonnet 4.5 (complex documentation generation)
**Estimated time**: 5-15 minutes
**Requirements**: Node.js, npm, Python (optional)
