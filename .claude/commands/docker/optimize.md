---
description: Optimize Docker image size, build time, and runtime performance with automated recommendations and fixes
argument-hint: [--target <size|speed|both>] [--auto-apply] [--analyze-only]
model: claude-sonnet-4-5-20250929
allowed-tools: Task, Read, Glob, Grep, Write, Bash
---

Docker Optimization: **${ARGUMENTS}**

## Optimizing Docker Configuration

Use the Task tool with subagent_type=docker-specialist to optimize your Docker setup with the following specifications:

### Input Parameters

**Optimization Target**: ${TARGET:-both} (size, speed, or both)
**Auto-Apply**: ${AUTO_APPLY:-false} (preview only vs auto-apply fixes)
**Analyze Only**: ${ANALYZE_ONLY:-false} (just show recommendations)

### Objectives

You are tasked with analyzing and optimizing Docker images and configurations for maximum efficiency. Your implementation must:

#### 1. Image Size Analysis

**Analyze Current Image**:

```bash
# Get image size and layer information
docker images myapp:latest
docker history myapp:latest --no-trunc

# Analyze each layer's contribution to size
docker history myapp:latest --format "{{.Size}}\t{{.CreatedBy}}" | \
  sort -h -r | head -20
```

**Common Bloat Sources**:

- Unnecessary build dependencies
- Package manager caches
- Temporary files not cleaned up
- Using full base images instead of slim/alpine
- Including source files in production image
- Large log files or artifacts

**Size Optimization Strategies**:

**Strategy 1: Use Alpine Base Images** (70-90% size reduction):

```dockerfile
# Before: 1.2 GB
FROM node:20
# ... rest of Dockerfile

# After: 180 MB
FROM node:20-alpine
# ... rest of Dockerfile

# Savings: ~1 GB (85% reduction)
```

**Strategy 2: Multi-Stage Builds** (50-80% reduction):

```dockerfile
# Before: Single-stage (800 MB)
FROM node:20-alpine
COPY package*.json ./
RUN npm install  # Includes devDependencies
COPY . .
RUN npm run build
CMD ["node", "dist/index.js"]

# After: Multi-stage (150 MB)
FROM node:20-alpine AS builder
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:20-alpine AS production
COPY package*.json ./
RUN npm ci --only=production && npm cache clean --force
COPY --from=builder /app/dist ./dist
CMD ["node", "dist/index.js"]

# Savings: 650 MB (81% reduction)
```

**Strategy 3: Clean Package Manager Caches**:

```dockerfile
# Before: Leaves cache (adds ~200 MB)
RUN npm install

# After: Cleans cache
RUN npm ci && npm cache clean --force
# OR
RUN apt-get update && apt-get install -y package && \
    rm -rf /var/lib/apt/lists/*

# Savings: ~200 MB per package manager
```

**Strategy 4: Use .dockerignore Effectively**:

```
# Reduces build context from 500 MB to 50 MB
node_modules/
.git/
*.md
test/
coverage/
.env
.DS_Store
```

**Strategy 5: Distroless Images** (minimal attack surface):

```dockerfile
# After build, use distroless for runtime
FROM gcr.io/distroless/nodejs20-debian11

COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules

CMD ["dist/index.js"]

# Benefits:
# - Smallest possible image (~50 MB)
# - No shell, package manager, or utilities
# - Minimal attack surface
```

#### 2. Build Time Optimization

**Analyze Build Performance**:

```bash
# Build with timing information
DOCKER_BUILDKIT=1 docker build \
  --progress=plain \
  --no-cache \
  -t myapp:latest . 2>&1 | tee build.log

# Identify slow steps
grep "DONE" build.log | awk '{print $2, $3, $4}'
```

**Build Speed Optimizations**:

**Optimization 1: Layer Caching** (10x faster rebuilds):

```dockerfile
# Before: Poor caching (everything rebuilds on code change)
COPY . .
RUN npm install
RUN npm run build

# After: Optimal caching (only rebuild what changed)
COPY package*.json ./
RUN npm ci  # ← Cached if package.json unchanged
COPY . .
RUN npm run build  # ← Only rebuilds if source changed

# Build time: 3 min → 15 sec (on code changes)
```

**Optimization 2: Parallel Builds with BuildKit**:

```dockerfile
# syntax=docker/dockerfile:1

# Enable BuildKit features
FROM node:20-alpine AS deps
RUN --mount=type=cache,target=/root/.npm \
    npm ci

FROM node:20-alpine AS builder
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN --mount=type=cache,target=/root/.npm \
    npm run build

# BuildKit features used:
# - Parallel stage execution
# - Build cache mounts
# - Improved layer caching
```

**Optimization 3: Use BuildKit Cache Mounts**:

```dockerfile
# Cache package manager downloads across builds
RUN --mount=type=cache,target=/root/.npm \
    --mount=type=cache,target=/root/.cache/pip \
    npm ci

# Result: Dependencies download once, cached forever
```

**Optimization 4: Multi-Platform Builds**:

```bash
# Build for multiple platforms in parallel
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --cache-from type=registry,ref=myapp:buildcache \
  --cache-to type=registry,ref=myapp:buildcache,mode=max \
  --push \
  -t myapp:latest .
```

#### 3. Runtime Performance Optimization

**Memory Optimization**:

```dockerfile
# Set Node.js memory limits
ENV NODE_OPTIONS="--max-old-space-size=512"

# Use efficient allocators
RUN apk add --no-cache libc6-compat
```

**Startup Time Optimization**:

```dockerfile
# Before: Cold start with npm (slow)
CMD ["npm", "start"]

# After: Direct node execution (fast)
CMD ["node", "dist/index.js"]

# Startup time: 5s → 1s
```

**CPU Optimization**:

```dockerfile
# Enable production mode
ENV NODE_ENV=production

# Pre-compile code if applicable
RUN npm run build

# Use clustering for multi-core utilization
CMD ["node", "-r", "cluster", "dist/index.js"]
```

#### 4. Automated Optimization Report

**Generate Optimization Report**:

```markdown
# Docker Optimization Report

## Current State

**Image**: myapp:latest
**Size**: 1.2 GB
**Build Time**: 5 minutes
**Layers**: 42

### Size Breakdown by Layer:
| Layer | Size | Command |
|-------|------|---------|
| 1 | 450 MB | FROM node:20 |
| 2 | 350 MB | RUN npm install |
| 3 | 250 MB | COPY . . |
| 4 | 150 MB | RUN npm run build |
| ... | ... | ... |

## Optimization Opportunities

### HIGH IMPACT (Implement First)

#### 1. Switch to Alpine Base Image
- **Current**: `FROM node:20` (450 MB)
- **Optimized**: `FROM node:20-alpine` (50 MB)
- **Savings**: 400 MB (89% reduction)
- **Effort**: Low (5 minutes)

```dockerfile
# Change line 1:
FROM node:20-alpine
```

#### 2. Implement Multi-Stage Build

- **Current**: Single stage with all dependencies
- **Optimized**: Separate build and runtime stages
- **Savings**: 300 MB (build dependencies removed)
- **Effort**: Medium (30 minutes)

```dockerfile
FROM node:20-alpine AS builder
# ... build steps ...

FROM node:20-alpine AS production
COPY --from=builder /app/dist ./dist
# ... runtime only ...
```

#### 3. Clean Package Manager Cache

- **Current**: npm cache retained (200 MB)
- **Optimized**: Clean cache after install
- **Savings**: 200 MB
- **Effort**: Low (2 minutes)

```dockerfile
RUN npm ci && npm cache clean --force
```

### MEDIUM IMPACT

#### 4. Optimize Layer Caching

- **Current**: Poor layer ordering
- **Optimized**: Cache-friendly order
- **Savings**: Build time 5 min → 30 sec (on code changes)
- **Effort**: Low (10 minutes)

```dockerfile
# Copy package files first (cached)
COPY package*.json ./
RUN npm ci

# Copy source last (changes frequently)
COPY . .
```

#### 5. Add .dockerignore

- **Current**: 500 MB build context
- **Optimized**: 50 MB build context
- **Savings**: Faster uploads, 90% context reduction
- **Effort**: Low (5 minutes)

```
node_modules/
.git/
test/
*.md
```

### LOW IMPACT (Nice to Have)

#### 6. Use Distroless Runtime

- **Current**: Alpine with shell and utilities
- **Optimized**: Distroless (runtime only)
- **Savings**: 30 MB + improved security
- **Effort**: High (60 minutes)

#### 7. Enable BuildKit Features

- **Savings**: Faster builds, better caching
- **Effort**: Low (add syntax header)

```dockerfile
# syntax=docker/dockerfile:1
```

## Optimized Dockerfile

**Before** (1.2 GB, 5 min build):

```dockerfile
FROM node:20
WORKDIR /app
COPY . .
RUN npm install
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

**After** (150 MB, 30 sec rebuild):

```dockerfile
# syntax=docker/dockerfile:1

FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN --mount=type=cache,target=/root/.npm npm ci
COPY . .
RUN npm run build

FROM node:20-alpine AS production
WORKDIR /app
RUN addgroup -g 1001 -S nodejs && adduser -S nodejs -u 1001
COPY package*.json ./
RUN npm ci --only=production && npm cache clean --force
COPY --from=builder --chown=nodejs:nodejs /app/dist ./dist
USER nodejs
EXPOSE 3000
HEALTHCHECK CMD node healthcheck.js
CMD ["node", "dist/index.js"]
```

## Expected Results

### Size Optimization

- **Before**: 1.2 GB
- **After**: 150 MB
- **Reduction**: 87.5%

### Build Time

- **Initial Build**: 5 min → 2 min (40% faster)
- **Rebuild (code change)**: 5 min → 30 sec (90% faster)
- **Rebuild (no change)**: 5 min → 5 sec (98% faster)

### Performance

- **Startup Time**: 5s → 1s
- **Memory Usage**: 300 MB → 150 MB
- **Security**: +4 improvements (non-root, minimal base, no cache, health check)

## Implementation Priority

**Quick Wins** (30 minutes total):

1. ✅ Switch to Alpine base image (5 min) → 400 MB saved
2. ✅ Clean npm cache (2 min) → 200 MB saved
3. ✅ Add .dockerignore (5 min) → Faster builds
4. ✅ Optimize layer order (10 min) → 90% faster rebuilds

**High Value** (2 hours):
5. ✅ Implement multi-stage build (30 min) → 300 MB saved
6. ✅ Add health checks (10 min) → Better orchestration
7. ✅ Run as non-root user (10 min) → Security
8. ✅ Enable BuildKit (5 min) → Faster builds

**Advanced** (4+ hours):
9. ⚠️ Distroless runtime (60 min) → 30 MB saved + security
10. ⚠️ Multi-platform builds (30 min) → ARM support

## Automated Fixes

Would you like to:

1. **Apply all quick wins** (auto-implement in 5 minutes)
2. **Apply quick wins + high value** (complete optimization)
3. **Preview changes only** (review before applying)
4. **Custom selection** (choose specific optimizations)

```

#### 5. Benchmarking and Validation

**Before/After Comparison**:
```bash
#!/bin/bash

# Benchmark script

echo "📊 Docker Optimization Benchmark"
echo "================================"

# Build original
echo "Building original Dockerfile..."
time docker build -t myapp:before -f Dockerfile.old . > /dev/null 2>&1
SIZE_BEFORE=$(docker images myapp:before --format "{{.Size}}")

# Build optimized
echo "Building optimized Dockerfile..."
time docker build -t myapp:after . > /dev/null 2>&1
SIZE_AFTER=$(docker images myapp:after --format "{{.Size}}")

# Compare
echo ""
echo "Results:"
echo "--------"
echo "Size Before: $SIZE_BEFORE"
echo "Size After:  $SIZE_AFTER"

# Calculate reduction
echo ""
echo "Memory usage comparison:"
docker stats --no-stream myapp:before myapp:after

# Startup time
echo ""
echo "Startup time comparison:"
time docker run --rm myapp:before node -e "console.log('Ready')"
time docker run --rm myapp:after node -e "console.log('Ready')"
```

**Continuous Monitoring**:

```yaml
# .github/workflows/docker-optimization.yml
name: Monitor Docker Image Size

on:
  push:
    branches: [main]

jobs:
  size-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build image
        run: docker build -t myapp:${{ github.sha }} .

      - name: Check image size
        run: |
          SIZE=$(docker images myapp:${{ github.sha }} --format "{{.Size}}")
          echo "Image size: $SIZE"

          # Fail if size exceeds threshold
          SIZE_MB=$(docker images myapp:${{ github.sha }} --format "{{.Size}}" | sed 's/MB//')
          if (( $(echo "$SIZE_MB > 300" | bc -l) )); then
            echo "❌ Image size $SIZE_MB MB exceeds 300 MB threshold"
            exit 1
          fi

          echo "✅ Image size within acceptable range"
```

### Implementation Steps

**Step 1: Analysis**

1. Scan existing Dockerfile
2. Analyze image layers and sizes
3. Identify optimization opportunities
4. Calculate potential savings

**Step 2: Generate Report**

1. Create detailed optimization report
2. Categorize by impact (high/medium/low)
3. Provide code snippets for each fix
4. Calculate ROI for each optimization

**Step 3: Apply Optimizations** (if auto-apply enabled)

1. Backup original Dockerfile
2. Apply optimizations in priority order
3. Validate syntax
4. Test build

**Step 4: Validation**

1. Build optimized image
2. Compare before/after metrics
3. Run smoke tests
4. Verify functionality

**Step 5: Documentation**

1. Update DOCKER.md with changes
2. Document new build process
3. Provide rollback instructions

### Output Requirements

**Generated Files**:

- `Dockerfile.optimized` - Optimized Dockerfile
- `Dockerfile.old.backup` - Original backup
- `.dockerignore` - Optimized ignore file
- `OPTIMIZATION_REPORT.md` - Detailed analysis
- `benchmark.sh` - Before/after comparison script

## ROI Impact

**Time Savings**:

- **Build time reduction**: 5 min → 30 sec (90%) = 9 builds/hour vs 60 builds/hour
- **CI/CD pipeline**: 30 min/day saved = 10 hours/month
- **Developer productivity**: Faster iteration

**Cost Savings**:

- **Storage costs**: 1.2 GB → 150 MB per image × 1000 images = 1 TB saved
- **Transfer costs**: 87% less bandwidth usage
- **Registry costs**: $50/month → $10/month

**Performance Improvements**:

- **Faster deployments**: 2 min pull → 15 sec pull
- **Better resource utilization**: 150 MB RAM vs 300 MB RAM
- **Improved startup times**: 5s → 1s

**Total Value**: $50,000/year

- CI/CD time savings: $25,000/year
- Infrastructure costs: $15,000/year
- Faster deployments: $10,000/year

## Success Criteria

✅ **Image size reduced by >70%**
✅ **Build time improved by >50%**
✅ **All optimizations validated**
✅ **No functionality regressions**
✅ **Documentation updated**

**Target Metrics**:

- Final image size: < 200 MB
- Build time (cached): < 1 minute
- Build time (no cache): < 5 minutes
- Startup time: < 3 seconds

## Next Steps

1. Review optimization report
2. Apply recommended changes
3. Test optimized image
4. Update CI/CD pipelines
5. Monitor performance metrics

---

**Optimization Status**: 🟢 Ready to Apply
**Potential Savings**: 87% size reduction, 90% build time reduction
**Annual ROI**: $50,000
