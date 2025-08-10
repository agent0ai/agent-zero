---
source: https://docs.docker.com/build/building/best-practices/
retrieved: 2025-08-09T14:35:39Z
fetch_method: document_query
agent: agent0
original_filename: docker_building_best_practices_official.md
content_type: technical_guide
verification_status: pending
---

# Docker Building Best Practices - Official Documentation

*Source: Docker Official Documentation*

## Overview

This comprehensive guide from Docker's official documentation covers best practices for building Docker images efficiently, securely, and maintainably. These practices help create production-ready containers that are optimized for size, security, and performance.

## Core Building Principles

### 1. Use Multi-Stage Builds

Multi-stage builds reduce final image size by creating cleaner separation between building and runtime environments.

**Benefits:**
- Smaller final images (only runtime dependencies included)
- Better separation of concerns
- Parallel build execution for efficiency
- Cleaner build process

**Example:**
```dockerfile
# Build stage
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

# Runtime stage
FROM node:18-alpine AS runtime
WORKDIR /app
COPY --from=builder /app/node_modules ./node_modules
COPY . .
EXPOSE 3000
CMD ["node", "server.js"]
```

#### Create Reusable Stages

For multiple images with common components, create reusable base stages:

```dockerfile
# Common base stage
FROM node:18-alpine AS base
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

# Development stage
FROM base AS development
RUN npm ci
COPY . .
CMD ["npm", "run", "dev"]

# Production stage
FROM base AS production
COPY . .
CMD ["npm", "start"]
```

### 2. Choose the Right Base Image

**Trusted Sources Priority:**
1. **Docker Official Images** - Curated, documented, regularly updated
2. **Verified Publisher Images** - High-quality images from Docker partners
3. **Docker-Sponsored Open Source** - Maintained by sponsored open source projects

**Selection Criteria:**
- **Minimal size** - Reduces attack surface and download time
- **Security updates** - Regular patching and maintenance
- **Documentation** - Clear usage guidelines
- **Community support** - Active maintenance and issue resolution

**Recommended Base Images:**
```dockerfile
# Alpine Linux (minimal, ~6MB)
FROM alpine:3.21

# Distroless (Google's minimal images)
FROM gcr.io/distroless/java:11

# Official language images
FROM python:3.11-slim
FROM node:18-alpine
FROM golang:1.21-alpine
```

### 3. Rebuild Images Frequently

**Why Rebuild:**
- Security patches in base images
- Updated dependencies
- Latest package versions

**Force Fresh Builds:**
```bash
# Bypass cache for fresh dependencies
docker build --no-cache -t my-image:latest .

# Pull latest base image
docker build --pull -t my-image:latest .
```

**Automated Rebuilds:**
```yaml
# GitHub Actions example
name: Rebuild Images
on:
  schedule:
    - cron: '0 2 * * 1'  # Weekly on Monday 2 AM
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build and push
        run: |
          docker build --no-cache -t ${{ secrets.REGISTRY }}/app:latest .
          docker push ${{ secrets.REGISTRY }}/app:latest
```

### 4. Optimize with .dockerignore

Exclude unnecessary files to reduce build context size and improve security.

**Example .dockerignore:**
```gitignore
# Version control
.git
.gitignore

# Documentation
*.md
README*
docs/

# Development files
.env.local
.env.development
node_modules/
__pycache__/
*.pyc

# IDE files
.vscode/
.idea/
*.swp
*.swo

# OS files
.DS_Store
Thumbs.db

# Build artifacts
dist/
build/
target/

# Logs
*.log
logs/

# Test files
test/
*.test.js
coverage/

# CI/CD
.github/
.gitlab-ci.yml
Jenkinsfile
```

### 5. Create Ephemeral Containers

**Principles:**
- Containers should be stateless
- Easy to stop, destroy, and recreate
- Minimal setup and configuration required
- Data persistence through volumes, not container filesystem

**Implementation:**
```dockerfile
# Store data in volumes, not container
VOLUME ["/data"]

# Use environment variables for configuration
ENV DATABASE_URL="postgresql://user:pass@db:5432/myapp"
ENV LOG_LEVEL="info"

# Avoid hardcoded paths
WORKDIR /app
COPY . .
```

### 6. Minimize Package Installation

**Avoid Unnecessary Packages:**
```dockerfile
# Bad - installs text editor in production
RUN apt-get update && apt-get install -y     python3     python3-pip     vim     curl

# Good - only essential packages
RUN apt-get update && apt-get install -y --no-install-recommends     python3     python3-pip     && rm -rf /var/lib/apt/lists/*
```

**Benefits:**
- Reduced image size
- Fewer security vulnerabilities
- Faster builds and deployments
- Lower resource consumption

### 7. Decouple Applications

**One Process Per Container:**
```dockerfile
# Web application container
FROM nginx:alpine
COPY nginx.conf /etc/nginx/nginx.conf
COPY dist/ /usr/share/nginx/html/
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

```dockerfile
# API container
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "app.py"]
```

**Container Orchestration:**
```yaml
# docker-compose.yml
version: '3.8'
services:
  web:
    build: ./web
    ports:
      - "80:80"
    depends_on:
      - api

  api:
    build: ./api
    ports:
      - "8000:8000"
    depends_on:
      - db

  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: myapp
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

### 8. Sort Multi-Line Arguments

**Maintainable Package Lists:**
```dockerfile
# Good - alphabetically sorted, easy to maintain
RUN apt-get update && apt-get install -y --no-install-recommends     build-essential     curl     git     libpq-dev     python3-dev     wget     && rm -rf /var/lib/apt/lists/*
```

**Benefits:**
- Easier to spot duplicates
- Simpler to add/remove packages
- Better code review experience
- Reduced merge conflicts

### 9. Leverage Build Cache

**Cache-Friendly Layer Ordering:**
```dockerfile
# Dependencies change less frequently - cache these layers
COPY requirements.txt .
RUN pip install -r requirements.txt

# Application code changes frequently - put last
COPY . .
```

**Cache Optimization Strategies:**
```dockerfile
# Multi-stage with dependency caching
FROM python:3.11-slim AS deps
COPY requirements.txt .
RUN pip install --user -r requirements.txt

FROM python:3.11-slim AS runtime
COPY --from=deps /root/.local /root/.local
COPY . .
ENV PATH=/root/.local/bin:$PATH
CMD ["python", "app.py"]
```

### 10. Pin Base Image Versions

**Version Pinning Strategies:**

**1. Tag Pinning (Flexible):**
```dockerfile
FROM python:3.11-slim  # Gets latest patch version
```

**2. Digest Pinning (Immutable):**
```dockerfile
FROM python:3.11-slim@sha256:a8560b36e8b8210634f77d9f7f9efd7ffa463e380b75e2e74aff4511df3ef88c
```

**3. Hybrid Approach:**
```dockerfile
# Pin to specific version with digest for reproducibility
FROM python:3.11.8-slim@sha256:specific-digest-here
```

**Automated Updates with Docker Scout:**
- Monitors for base image updates
- Creates pull requests for digest updates
- Provides security vulnerability scanning
- Ensures compliance with update policies

### 11. CI/CD Integration

**GitHub Actions Example:**
```yaml
name: Build and Test Docker Image

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v4

    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v3

    - name: Build image
      uses: docker/build-push-action@v5
      with:
        context: .
        push: false
        tags: myapp:test
        cache-from: type=gha
        cache-to: type=gha,mode=max

    - name: Test image
      run: |
        docker run --rm myapp:test python -m pytest

    - name: Security scan
      uses: docker/scout-action@v1
      with:
        command: cves
        image: myapp:test
```

## Dockerfile Instruction Best Practices

### FROM

**Choose Minimal Base Images:**
```dockerfile
# Prefer Alpine for smaller size
FROM python:3.11-alpine

# Or use distroless for security
FROM gcr.io/distroless/python3

# Official images are recommended
FROM node:18-alpine
```

### LABEL

**Comprehensive Metadata:**
```dockerfile
LABEL maintainer="team@company.com"       version="1.0.0"       description="Production web application"       org.opencontainers.image.source="https://github.com/company/app"       org.opencontainers.image.documentation="https://docs.company.com/app"       org.opencontainers.image.licenses="MIT"
```

### RUN

**Efficient Package Management:**
```dockerfile
# Combine commands to reduce layers
RUN apt-get update     && apt-get install -y --no-install-recommends         build-essential         curl         git     && apt-get clean     && rm -rf /var/lib/apt/lists/*
```

**Using Here Documents:**
```dockerfile
RUN <<EOF
apt-get update
apt-get install -y --no-install-recommends     python3     python3-pip
apt-get clean
rm -rf /var/lib/apt/lists/*
EOF
```

**Pipeline Safety:**
```dockerfile
# Ensure pipeline failures are caught
RUN set -o pipefail &&     curl -fsSL https://example.com/script.sh | bash

# Or use explicit shell
RUN ["/bin/bash", "-c", "set -o pipefail && curl -fsSL https://example.com/script.sh | bash"]
```

### apt-get Best Practices

**Proper Package Management:**
```dockerfile
# Always combine update and install
RUN apt-get update && apt-get install -y --no-install-recommends     package1     package2     package3=1.3.*     && rm -rf /var/lib/apt/lists/*
```

**Why This Pattern:**
- `apt-get update` refreshes package lists
- `--no-install-recommends` reduces package bloat
- Version pinning (`package3=1.3.*`) for reproducibility
- Cache cleanup (`rm -rf /var/lib/apt/lists/*`) reduces image size
- Single RUN instruction reduces layers

### CMD

**Executable Form Preferred:**
```dockerfile
# Good - exec form
CMD ["python", "app.py"]

# Good - with parameters
CMD ["nginx", "-g", "daemon off;"]

# For interactive shells
CMD ["python"]
CMD ["bash"]
```

### EXPOSE

**Document Port Usage:**
```dockerfile
# Web server
EXPOSE 80 443

# Database
EXPOSE 5432

# Application with health check
EXPOSE 8000 8080
```

### ENV

**Environment Configuration:**
```dockerfile
# Application configuration
ENV APP_ENV=production     LOG_LEVEL=info     DATABASE_URL="postgresql://user:pass@db:5432/app"

# Path updates
ENV PATH="/app/bin:$PATH"

# Version management
ENV PYTHON_VERSION=3.11.8     PIP_VERSION=23.3.1
RUN pip install --upgrade pip==$PIP_VERSION
```

**Environment Variable Scope:**
```dockerfile
# Variables persist across layers
ENV ADMIN_USER="admin"
RUN echo $ADMIN_USER > /tmp/user

# Use RUN for temporary variables
RUN export TEMP_VAR="value" &&     echo $TEMP_VAR > /tmp/temp &&     unset TEMP_VAR
```

### COPY vs ADD

**COPY for Simple File Operations:**
```dockerfile
# Copy application files
COPY src/ /app/src/
COPY requirements.txt /app/

# Multi-stage copy
COPY --from=builder /app/dist /app/dist
```

**ADD for Remote Resources:**
```dockerfile
# Download and extract archives
ADD https://releases.example.com/app-v1.0.tar.gz /tmp/

# With checksum validation
ADD --checksum=sha256:abc123...     https://example.com/file.tar.gz /tmp/
```

**Bind Mounts for Temporary Files:**
```dockerfile
# Instead of COPY for temporary files
RUN --mount=type=bind,source=requirements.txt,target=/tmp/requirements.txt     pip install --requirement /tmp/requirements.txt
```

### ENTRYPOINT

**Main Command Definition:**
```dockerfile
# Command-line tool pattern
ENTRYPOINT ["s3cmd"]
CMD ["--help"]

# Usage: docker run myimage ls s3://bucket
```

**Helper Script Pattern:**
```dockerfile
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["app"]
```

**Example Entrypoint Script:**
```bash
#!/bin/bash
set -e

# Initialize application if needed
if [ "$1" = 'app' ]; then
    # Setup database
    python manage.py migrate

    # Start application
    exec python app.py
fi

# Execute any other command
exec "$@"
```

### USER

**Security Best Practices:**
```dockerfile
# Create non-root user
RUN groupadd -r appuser &&     useradd --no-log-init -r -g appuser appuser

# Set ownership
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser
```

**Explicit UID/GID:**
```dockerfile
# For consistent user mapping
RUN groupadd -r -g 1001 appuser &&     useradd --no-log-init -r -u 1001 -g appuser appuser

USER 1001:1001
```

### WORKDIR

**Absolute Paths:**
```dockerfile
# Good - absolute path
WORKDIR /app

# Avoid relative paths and cd commands
# Bad: RUN cd /app && do-something
```

### VOLUME

**Data Persistence:**
```dockerfile
# Database data
VOLUME ["/var/lib/postgresql/data"]

# Application uploads
VOLUME ["/app/uploads"]

# Configuration
VOLUME ["/etc/myapp"]
```

## Advanced Optimization Techniques

### Multi-Architecture Builds

```dockerfile
# syntax=docker/dockerfile:1
FROM --platform=$BUILDPLATFORM golang:1.21-alpine AS builder
ARG TARGETPLATFORM
ARG BUILDPLATFORM
RUN echo "Building on $BUILDPLATFORM, targeting $TARGETPLATFORM"

WORKDIR /src
COPY . .
RUN CGO_ENABLED=0 GOOS=${TARGETOS} GOARCH=${TARGETARCH}     go build -o /app/server .

FROM alpine:3.21
RUN apk --no-cache add ca-certificates
COPY --from=builder /app/server /server
EXPOSE 8080
CMD ["/server"]
```

**Build Command:**
```bash
docker buildx build --platform linux/amd64,linux/arm64 -t myapp:latest .
```

### Build Secrets

```dockerfile
# syntax=docker/dockerfile:1
FROM alpine:3.21

# Use build secrets for sensitive data
RUN --mount=type=secret,id=api_key     API_KEY=$(cat /run/secrets/api_key) &&     curl -H "Authorization: Bearer $API_KEY" https://api.example.com/data
```

**Build with secrets:**
```bash
echo "secret-api-key" | docker build --secret id=api_key,src=- .
```

### Cache Mounts

```dockerfile
# Package manager cache
RUN --mount=type=cache,target=/var/cache/apt     --mount=type=cache,target=/var/lib/apt     apt-get update &&     apt-get install -y python3-pip

# Language-specific caches
RUN --mount=type=cache,target=/root/.cache/pip     pip install -r requirements.txt

RUN --mount=type=cache,target=/root/.npm     npm ci --only=production
```

## Security Best Practices

### Minimal Attack Surface

```dockerfile
# Use distroless for minimal attack surface
FROM gcr.io/distroless/python3-debian12
COPY --from=builder /app /app
WORKDIR /app
EXPOSE 8000
CMD ["python", "app.py"]
```

### Vulnerability Scanning

```bash
# Scan with Docker Scout
docker scout cves myapp:latest

# Scan with Trivy
trivy image myapp:latest

# Scan with Snyk
snyk container test myapp:latest
```

### Content Trust

```bash
# Enable content trust
export DOCKER_CONTENT_TRUST=1

# Build and push signed images
docker build -t myregistry.com/myapp:latest .
docker push myregistry.com/myapp:latest
```

## Performance Optimization

### Layer Optimization

```dockerfile
# Combine related operations
RUN apt-get update &&     apt-get install -y --no-install-recommends         build-essential         python3-dev &&     pip install --no-cache-dir -r requirements.txt &&     apt-get purge -y build-essential python3-dev &&     apt-get autoremove -y &&     rm -rf /var/lib/apt/lists/*
```

### Build Context Optimization

```dockerfile
# Use .dockerignore to exclude unnecessary files
# Copy only what's needed
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy source code last (changes most frequently)
COPY src/ ./src/
```

### Parallel Builds

```dockerfile
# syntax=docker/dockerfile:1
FROM alpine:3.21 AS base
RUN apk add --no-cache ca-certificates

# Parallel stage 1
FROM base AS deps1
RUN apk add --no-cache python3 py3-pip

# Parallel stage 2
FROM base AS deps2
RUN apk add --no-cache nodejs npm

# Combine results
FROM base AS final
COPY --from=deps1 /usr/bin/python3 /usr/bin/
COPY --from=deps2 /usr/bin/node /usr/bin/
```

## Monitoring and Observability

### Health Checks

```dockerfile
# Application health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3     CMD curl -f http://localhost:8000/health || exit 1

# Database health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3     CMD pg_isready -U $POSTGRES_USER -d $POSTGRES_DB || exit 1
```

### Logging Configuration

```dockerfile
# Configure logging
ENV PYTHONUNBUFFERED=1
ENV LOG_LEVEL=info

# Use structured logging
RUN pip install structlog
```

### Metrics and Tracing

```dockerfile
# Add observability tools
RUN pip install prometheus-client opentelemetry-api

# Expose metrics port
EXPOSE 9090
```

## Production Deployment Patterns

### Blue-Green Deployment

```yaml
# docker-compose.blue-green.yml
version: '3.8'
services:
  app-blue:
    image: myapp:v1.0
    ports:
      - "8001:8000"

  app-green:
    image: myapp:v1.1
    ports:
      - "8002:8000"

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - app-blue
      - app-green
```

### Rolling Updates

```yaml
# docker-compose.yml with rolling updates
version: '3.8'
services:
  app:
    image: myapp:latest
    deploy:
      replicas: 3
      update_config:
        parallelism: 1
        delay: 10s
        order: start-first
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
```

### Resource Limits

```yaml
services:
  app:
    image: myapp:latest
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M
```

## Troubleshooting and Debugging

### Debug Images

```dockerfile
# Multi-stage with debug variant
FROM python:3.11-slim AS base
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

# Production image
FROM base AS production
COPY . .
USER 1001
CMD ["python", "app.py"]

# Debug image with additional tools
FROM base AS debug
RUN apt-get update && apt-get install -y     curl     vim     strace     && rm -rf /var/lib/apt/lists/*
COPY . .
CMD ["python", "app.py"]
```

### Build Debugging

```bash
# Debug build process
docker build --progress=plain --no-cache .

# Inspect intermediate layers
docker build --target=debug -t myapp:debug .
docker run -it myapp:debug /bin/bash

# Build with BuildKit debugging
DOCKER_BUILDKIT=1 docker build --progress=plain .
```

## Conclusion

Effective Docker image building requires attention to:

1. **Security** - Use trusted base images, non-root users, and regular updates
2. **Performance** - Optimize layers, leverage caching, and minimize image size
3. **Maintainability** - Clear documentation, consistent patterns, and automated testing
4. **Reliability** - Proper error handling, health checks, and resource management
5. **Observability** - Structured logging, metrics, and debugging capabilities

By following these best practices, you can create Docker images that are secure, efficient, and production-ready. Regular review and updates of your Dockerfile practices ensure continued alignment with evolving security standards and performance optimizations.

## Additional Resources

- [Docker Official Documentation](https://docs.docker.com/)
- [Dockerfile Reference](https://docs.docker.com/reference/dockerfile/)
- [Docker Build Cache](https://docs.docker.com/build/cache/)
- [Multi-stage Builds](https://docs.docker.com/build/building/multi-stage/)
- [Docker Scout Security](https://docs.docker.com/scout/)
- [BuildKit Advanced Features](https://docs.docker.com/build/buildkit/)
