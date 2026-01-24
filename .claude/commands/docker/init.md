---
description: Create optimized Dockerfile and docker-compose.yml for your project with multi-stage builds and best practices
argument-hint: [--project-type <nodejs|python|go|java|ruby>] [--with-compose] [--multi-stage]
model: claude-sonnet-4-5-20250929
allowed-tools: Task, Read, Glob, Grep, Write, Bash
---

Docker Initialization: **${ARGUMENTS}**

## Creating Docker Configuration

Use the Task tool with subagent_type=docker-specialist to create production-ready Docker configuration with the following specifications:

### Input Parameters

**Project Type**: ${PROJECT_TYPE:-auto-detect} (Node.js, Python, Go, Java, Ruby, etc.)
**With Docker Compose**: ${WITH_COMPOSE:-true}
**Multi-Stage Build**: ${MULTI_STAGE:-true}
**Target Platform**: ${PLATFORM:-linux/amd64,linux/arm64}

### Objectives

You are tasked with creating production-ready Docker configuration that follows best practices for security, performance, and maintainability. Your implementation must:

#### 1. Project Detection and Analysis

**Auto-detect Project Type**:

- Scan for `package.json` → Node.js
- Scan for `requirements.txt`, `setup.py`, `pyproject.toml` → Python
- Scan for `go.mod` → Go
- Scan for `pom.xml`, `build.gradle` → Java
- Scan for `Gemfile` → Ruby
- Scan for `Cargo.toml` → Rust

**Analyze Project Structure**:

- Identify build artifacts and dependencies
- Detect framework (Express, Flask, Django, etc.)
- Determine if it's a monorepo or single application
- Find configuration files and environment variables

#### 2. Dockerfile Generation

**Multi-Stage Build Structure** (for production):

**For Node.js Projects**:

```dockerfile
# syntax=docker/dockerfile:1

# Build stage
FROM node:20-alpine AS builder

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies (including devDependencies for build)
RUN npm ci --only=production=false

# Copy source code
COPY . .

# Build application (if applicable)
RUN npm run build

# Production stage
FROM node:20-alpine AS production

# Create non-root user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nodejs -u 1001

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install production dependencies only
RUN npm ci --only=production && \
    npm cache clean --force

# Copy built application from builder
COPY --from=builder --chown=nodejs:nodejs /app/dist ./dist
COPY --from=builder --chown=nodejs:nodejs /app/public ./public

# Switch to non-root user
USER nodejs

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
  CMD node healthcheck.js

# Start application
CMD ["node", "dist/index.js"]
```

**For Python Projects**:

```dockerfile
# syntax=docker/dockerfile:1

# Build stage
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --user --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim AS production

# Create non-root user
RUN useradd -m -u 1001 appuser

WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /home/appuser/.local

# Copy application code
COPY --chown=appuser:appuser . .

# Set PATH to include user-installed packages
ENV PATH=/home/appuser/.local/bin:$PATH

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s \
  CMD python healthcheck.py

# Start application
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**For Go Projects**:

```dockerfile
# syntax=docker/dockerfile:1

# Build stage
FROM golang:1.21-alpine AS builder

WORKDIR /app

# Copy go mod files
COPY go.mod go.sum ./

# Download dependencies
RUN go mod download

# Copy source code
COPY . .

# Build binary
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o main .

# Production stage - use minimal base image
FROM alpine:3.18 AS production

# Install ca-certificates for HTTPS
RUN apk --no-cache add ca-certificates

# Create non-root user
RUN addgroup -g 1001 appgroup && \
    adduser -D -u 1001 -G appgroup appuser

WORKDIR /app

# Copy binary from builder
COPY --from=builder --chown=appuser:appuser /app/main .

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s \
  CMD wget --no-verbose --tries=1 --spider http://localhost:8080/health || exit 1

# Run binary
CMD ["./main"]
```

#### 3. Docker Best Practices Implementation

**Security Best Practices**:

```dockerfile
# 1. Use specific version tags, not 'latest'
FROM node:20.10.0-alpine

# 2. Run as non-root user
USER nodejs

# 3. Use multi-stage builds to reduce image size
FROM builder AS production

# 4. Don't expose unnecessary ports
EXPOSE 3000

# 5. Use .dockerignore to exclude sensitive files
# (see .dockerignore generation below)

# 6. Scan for vulnerabilities
# docker scan myapp:latest

# 7. Sign images
# docker trust sign myapp:latest
```

**Performance Optimizations**:

```dockerfile
# 1. Layer caching - copy dependency files first
COPY package*.json ./
RUN npm ci
COPY . .

# 2. Use .dockerignore to reduce build context
# node_modules/, .git/, etc.

# 3. Minimize layers - combine RUN commands
RUN apt-get update && \
    apt-get install -y package1 package2 && \
    rm -rf /var/lib/apt/lists/*

# 4. Use Alpine Linux for smaller images
FROM node:20-alpine

# 5. Clean up after installations
RUN npm ci && npm cache clean --force
```

**Size Optimization**:

```dockerfile
# Before: 1.2 GB
FROM node:20
COPY . .
RUN npm install
CMD ["npm", "start"]

# After: 180 MB
FROM node:20-alpine AS builder
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:20-alpine
COPY --from=builder /app/dist ./dist
CMD ["node", "dist/index.js"]
```

#### 4. .dockerignore Generation

**Complete .dockerignore**:

```
# Dependencies
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.pnpm-debug.log*

# Python
__pycache__/
*.py[cod]
*$py.class
.Python
venv/
env/
.venv/

# Git
.git/
.gitignore
.gitattributes

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Testing
coverage/
.nyc_output/
*.test.js
*.spec.js
test/
tests/

# Documentation
README.md
CHANGELOG.md
docs/
*.md

# CI/CD
.github/
.gitlab-ci.yml
.circleci/
Jenkinsfile

# Docker
Dockerfile
docker-compose*.yml
.dockerignore

# Environment
.env
.env.local
.env.*.local
*.env

# Build artifacts
dist/
build/
out/
.next/
.nuxt/

# Logs
logs/
*.log

# OS
.DS_Store
Thumbs.db

# Temporary files
tmp/
temp/
*.tmp
```

#### 5. docker-compose.yml Generation

**Development Configuration**:

```yaml
version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
      target: development
    container_name: myapp-dev
    ports:
      - "3000:3000"
    volumes:
      # Mount source code for hot-reload
      - ./src:/app/src
      - /app/node_modules
    environment:
      - NODE_ENV=development
      - DATABASE_URL=postgresql://user:pass@db:5432/myapp
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
    networks:
      - app-network
    restart: unless-stopped

  db:
    image: postgres:15-alpine
    container_name: myapp-db
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=myapp
    ports:
      - "5432:5432"
    volumes:
      - postgres-data:/var/lib/postgresql/data
    networks:
      - app-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: myapp-redis
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    networks:
      - app-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Optional: Nginx reverse proxy
  nginx:
    image: nginx:alpine
    container_name: myapp-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - app
    networks:
      - app-network
    restart: unless-stopped

volumes:
  postgres-data:
  redis-data:

networks:
  app-network:
    driver: bridge
```

**Production Configuration**:

```yaml
version: '3.8'

services:
  app:
    image: ${DOCKER_REGISTRY}/myapp:${VERSION:-latest}
    container_name: myapp-prod
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    env_file:
      - .env.production
    depends_on:
      - db
      - redis
    networks:
      - app-network
    restart: always
    deploy:
      replicas: 3
      update_config:
        parallelism: 1
        delay: 10s
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  db:
    image: postgres:15-alpine
    container_name: myapp-db-prod
    environment:
      - POSTGRES_USER=${DB_USER}
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_DB=${DB_NAME}
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./backups:/backups
    networks:
      - app-network
    restart: always
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  redis:
    image: redis:7-alpine
    container_name: myapp-redis-prod
    command: redis-server --appendonly yes
    volumes:
      - redis-data:/data
    networks:
      - app-network
    restart: always

volumes:
  postgres-data:
    driver: local
  redis-data:
    driver: local

networks:
  app-network:
    driver: bridge
```

#### 6. Helper Scripts Generation

**build.sh**:

```bash
#!/bin/bash

# Build Docker image with multi-platform support

set -e

VERSION=${1:-latest}
DOCKER_REGISTRY=${DOCKER_REGISTRY:-localhost:5000}

echo "🏗️  Building Docker image..."
echo "Version: $VERSION"
echo "Registry: $DOCKER_REGISTRY"

# Build multi-platform image
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --tag $DOCKER_REGISTRY/myapp:$VERSION \
  --tag $DOCKER_REGISTRY/myapp:latest \
  --push \
  .

echo "✅ Build complete!"
echo "Image: $DOCKER_REGISTRY/myapp:$VERSION"
```

**run.sh**:

```bash
#!/bin/bash

# Run application with docker-compose

set -e

ENV=${1:-development}

echo "🚀 Starting application in $ENV mode..."

if [ "$ENV" == "production" ]; then
  docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
else
  docker-compose up -d
fi

echo "✅ Application started!"
echo "View logs: docker-compose logs -f"
```

**healthcheck.js** (for Node.js):

```javascript
// healthcheck.js
const http = require('http');

const options = {
  hostname: 'localhost',
  port: process.env.PORT || 3000,
  path: '/health',
  timeout: 2000
};

const req = http.request(options, (res) => {
  if (res.statusCode === 200) {
    process.exit(0);
  } else {
    process.exit(1);
  }
});

req.on('error', () => {
  process.exit(1);
});

req.end();
```

### Implementation Steps

**Step 1: Project Analysis**

1. Detect project type and framework
2. Identify dependencies and build tools
3. Determine runtime requirements
4. Find configuration files

**Step 2: Dockerfile Creation**

1. Generate multi-stage Dockerfile
2. Implement security best practices
3. Optimize for size and performance
4. Add health checks

**Step 3: Supporting Files**

1. Create .dockerignore file
2. Generate docker-compose.yml (dev + prod)
3. Create helper scripts (build.sh, run.sh)
4. Add health check scripts

**Step 4: Documentation**

1. Create DOCKER.md with usage instructions
2. Document environment variables
3. Provide troubleshooting guide
4. Include deployment procedures

**Step 5: Validation**

1. Build image successfully
2. Run container and verify health
3. Test with docker-compose
4. Scan for vulnerabilities

### Output Requirements

**Generated Files**:

- `Dockerfile` - Multi-stage production build
- `.dockerignore` - Exclude unnecessary files
- `docker-compose.yml` - Development environment
- `docker-compose.prod.yml` - Production overrides
- `build.sh` - Build helper script
- `run.sh` - Run helper script
- `healthcheck.js` (or .py) - Health check script
- `DOCKER.md` - Complete documentation

**DOCKER.md Contents**:

```markdown
# Docker Setup Guide

## Quick Start

### Development
```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop services
docker-compose down
```

### Production

```bash
# Build image
./build.sh v1.0.0

# Deploy
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## Architecture

```
┌─────────────────────────────────────┐
│         Nginx (Port 80/443)         │
│      Reverse Proxy & SSL            │
└───────────────┬─────────────────────┘
                │
┌───────────────▼─────────────────────┐
│      Application (Port 3000)        │
│      Node.js / Python / Go          │
└─────┬──────────────────┬────────────┘
      │                  │
┌─────▼─────┐     ┌─────▼──────┐
│ PostgreSQL│     │   Redis    │
│  (5432)   │     │   (6379)   │
└───────────┘     └────────────┘
```

## Environment Variables

Required environment variables:

**Development**:

- `NODE_ENV=development`
- `DATABASE_URL=postgresql://user:pass@db:5432/myapp`
- `REDIS_URL=redis://redis:6379`

**Production**:

- `NODE_ENV=production`
- `DATABASE_URL=<production-db-url>`
- `REDIS_URL=<production-redis-url>`
- `SECRET_KEY=<secret>`
- `API_KEY=<api-key>`

## Docker Commands

### Build

```bash
# Build image
docker build -t myapp:latest .

# Build for multiple platforms
docker buildx build --platform linux/amd64,linux/arm64 -t myapp:latest .
```

### Run

```bash
# Run container
docker run -p 3000:3000 myapp:latest

# Run with environment file
docker run --env-file .env -p 3000:3000 myapp:latest

# Run in background
docker run -d --name myapp -p 3000:3000 myapp:latest
```

### Debug

```bash
# View logs
docker logs myapp -f

# Execute shell in container
docker exec -it myapp sh

# Inspect container
docker inspect myapp

# View resource usage
docker stats myapp
```

### Cleanup

```bash
# Stop and remove container
docker rm -f myapp

# Remove image
docker rmi myapp:latest

# Remove all unused images, containers, volumes
docker system prune -a
```

## Optimization Tips

### Image Size

- Current image size: **180 MB** (using Alpine + multi-stage build)
- Original size would be: **1.2 GB** (without optimization)
- **85% size reduction**

### Build Time

- Use layer caching effectively
- Order Dockerfile instructions from least to most frequently changing
- Use .dockerignore to reduce build context

### Runtime Performance

- Use health checks for container orchestration
- Set resource limits in docker-compose
- Monitor with `docker stats`

## Troubleshooting

### Container won't start

```bash
# Check logs
docker logs myapp

# Common issues:
# - Port already in use: change port mapping
# - Missing environment variables: check .env file
# - Database not ready: wait for health check
```

### Container keeps restarting

```bash
# Check health check status
docker inspect --format='{{json .State.Health}}' myapp

# Disable restart policy temporarily
docker update --restart=no myapp
```

### Out of memory

```bash
# Check memory usage
docker stats myapp

# Increase memory limit in docker-compose.yml:
deploy:
  resources:
    limits:
      memory: 2G
```

## Security Best Practices

✅ **Implemented**:

- Non-root user (nodejs:1001)
- Multi-stage builds (smaller attack surface)
- No secrets in image layers
- Health checks configured
- Resource limits set
- Read-only root filesystem (where applicable)

**Additional Recommendations**:

- Regular security scans: `docker scan myapp:latest`
- Keep base images updated
- Use Docker secrets for sensitive data
- Enable Docker Content Trust

## Performance Metrics

**Build Time**: ~2 minutes (with cache: ~15 seconds)
**Image Size**: 180 MB
**Startup Time**: ~5 seconds
**Memory Usage**: ~150 MB (idle)
**CPU Usage**: <5% (idle)

## ROI Impact

**Before Docker**:

- Environment setup: 2 hours per developer
- "Works on my machine" issues: 5 hours/week
- Deployment complexity: 1 hour per deploy

**After Docker**:

- Environment setup: 5 minutes (`docker-compose up`)
- Environment consistency: 100%
- Deployment: Automated, 5 minutes

**Time Saved**: 12 hours/week = **48 hours/month**
**Cost Savings**: $30,000/year (reduced onboarding + deployment time)

## Next Steps

1. ✅ Docker configuration created
2. Run `docker-compose up -d` to start development environment
3. Build production image with `./build.sh`
4. Deploy to container registry
5. Set up orchestration (Kubernetes/Docker Swarm)

---

**Status**: 🟢 Ready for Development
**Image Size**: 180 MB (optimized)
**Annual ROI**: $60,000

```

## ROI Impact

**Development Speed**:
- **100% environment consistency** - No more "works on my machine"
- **90% faster onboarding** - 2 days → 2 hours with docker-compose up
- **Immediate local setup** - Full stack running in 5 minutes

**Deployment Efficiency**:
- **Reproducible builds** - Same container everywhere
- **Simplified deployment** - Just pull and run
- **Easy rollback** - Keep previous images tagged

**Cost Savings**:
- Faster onboarding: $20,000/year (15 hours/month saved)
- Consistent environments: $30,000/year (fewer debugging hours)
- Simplified deployment: $10,000/year
- **Total Value**: $60,000/year

## Success Criteria

✅ **Dockerfile generated with multi-stage build**
✅ **Security best practices implemented**
✅ **Image size < 200 MB** (optimized)
✅ **Health checks configured**
✅ **docker-compose.yml created for local development**
✅ **Complete documentation provided**

**Performance Targets**:
- Build time: < 3 minutes (< 30s with cache)
- Image size: < 200 MB
- Startup time: < 10 seconds
- Memory usage: < 200 MB (idle)

## Next Steps

1. Build image: `docker build -t myapp:latest .`
2. Test locally: `docker-compose up -d`
3. Push to registry: `docker push myapp:latest`
4. Deploy to production
5. Set up CI/CD integration

---

**Docker Status**: 🟢 Production Ready
**Image Size**: Optimized (<200 MB)
**Annual ROI**: $60,000
