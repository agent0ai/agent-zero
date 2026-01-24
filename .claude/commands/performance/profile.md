---
description: Profile application performance and identify bottlenecks
argument-hint: [--service <service-name>] [--duration <seconds>]
model: claude-sonnet-4-5-20250929
allowed-tools: Task, Bash, Write
---

Profile performance: **${ARGUMENTS}**

## Performance Profiling

**Analyzes**:

- CPU usage and hotspots
- Memory consumption and leaks
- Database query performance
- API response times
- Network latency
- Bundle size and load time

Routes to **web-performance-optimizer** + **gcp-monitoring-sre**:

```javascript
await Task({
  subagent_type: 'web-performance-optimizer',
  description: 'Profile application performance',
  prompt: `Profile performance for: ${SERVICE_NAME || 'application'}

Duration: ${DURATION || '60'} seconds

Execute comprehensive performance profiling:

## 1. CPU Profiling

### Backend (Node.js/Python)

\`\`\`bash
# Node.js - Use clinic.js
npx clinic doctor -- node app.js

# Or use built-in profiler
node --prof app.js
# Run load test
# Stop and analyze
node --prof-process isolate-*.log > cpu-profile.txt

# Python - Use cProfile
python -m cProfile -o profile.stats app.py
# Analyze
python -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumulative'); p.print_stats(20)"
\`\`\`

### Frontend

\`\`\`bash
# Use Lighthouse CI
npm install -g @lhci/cli
lhci collect --url=https://\${DOMAIN}
lhci upload

# Or Chrome DevTools via Puppeteer
node scripts/performance-profile.js
\`\`\`

**Analyze CPU Hotspots**:
- Functions consuming >10% CPU
- Tight loops
- Synchronous blocking operations
- Inefficient algorithms

## 2. Memory Profiling

### Detect Memory Leaks

\`\`\`bash
# Node.js heap snapshot
node --inspect app.js
# Connect Chrome DevTools
# Take heap snapshots over time
# Compare for leaks

# Python memory profiler
pip install memory_profiler
python -m memory_profiler app.py
\`\`\`

**Check for**:
- Growing heap size over time
- Unreleased event listeners
- Unclosed database connections
- Large object retention
- Circular references

**Memory Limits**:
- Cloud Run: 512MB-4GB (configure appropriately)
- Heap usage should stay <80% of limit

## 3. Database Query Performance

### Analyze Slow Queries

\`\`\`bash
# PostgreSQL/Cloud SQL - Find slow queries
gcloud sql operations list --instance=\${INSTANCE_NAME} \\
  --filter="operationType=QUERY AND duration>1000"

# Or enable slow query log
ALTER SYSTEM SET log_min_duration_statement = 1000; -- Log queries >1s

# Analyze query plans
EXPLAIN ANALYZE SELECT * FROM users WHERE email = 'user@example.com';
\`\`\`

**Optimize**:
- Add indexes on frequently queried columns
- Use query result caching
- Batch operations instead of N+1 queries
- Use connection pooling
- Denormalize if appropriate

**Performance Targets**:
- Query time: <100ms (95th percentile)
- Index hit ratio: >99%
- Connection pool utilization: 50-80%

## 4. API Response Time Analysis

### Measure Endpoint Performance

\`\`\`bash
# Use GCP Cloud Trace
gcloud trace list --limit=1000 \\
  --filter="spanName:'/api/*'" \\
  --format="table(traceId, spanName, duration)"

# Analyze percentiles
\`\`\`

**Break down response time**:
\`\`\`
Total Response Time: 450ms
├─ Network: 20ms (4%)
├─ Backend processing: 380ms (84%)
│  ├─ Database queries: 250ms (66%)
│  ├─ External API calls: 100ms (26%)
│  └─ Business logic: 30ms (8%)
└─ Rendering: 50ms (11%)
\`\`\`

**Optimization Priorities**:
1. Fix >100ms database queries (biggest impact)
2. Parallelize external API calls
3. Add caching layers

## 5. Frontend Performance

### Core Web Vitals

\`\`\`bash
# Run Lighthouse
lighthouse https://\${DOMAIN} \\
  --output json \\
  --output-path ./lighthouse-report.json

# Extract Core Web Vitals
cat lighthouse-report.json | jq '.audits | {
  LCP: .["largest-contentful-paint"].displayValue,
  FID: .["max-potential-fid"].displayValue,
  CLS: .["cumulative-layout-shift"].displayValue
}'
\`\`\`

**Targets** (75th percentile):
- LCP (Largest Contentful Paint): <2.5s
- FID (First Input Delay): <100ms
- CLS (Cumulative Layout Shift): <0.1

### Bundle Size Analysis

\`\`\`bash
# Webpack bundle analyzer
npm run build
npx webpack-bundle-analyzer dist/stats.json

# Check total size
du -sh dist/
\`\`\`

**Optimization**:
- Total bundle: <200KB (gzipped)
- Code splitting by route
- Lazy load below-the-fold content
- Remove unused dependencies
- Use tree shaking

## 6. Network Performance

### Check CDN and Caching

\`\`\`bash
# Test response headers
curl -I https://\${DOMAIN}/assets/app.js

# Check:
# - Cache-Control header
# - ETag/Last-Modified
# - Content-Encoding: gzip
# - CDN hit/miss
\`\`\`

**Optimize**:
- Enable gzip/brotli compression
- Set cache headers (static assets: 1 year, HTML: no-cache)
- Use CDN (Cloud CDN)
- Preload critical resources
- HTTP/2 server push

## 7. GCP Cloud Monitoring Metrics

### Query Performance Metrics

\`\`\`bash
# Get CPU usage over last hour
gcloud monitoring time-series list \\
  --filter='metric.type="run.googleapis.com/container/cpu/utilizations"' \\
  --format=json

# Get memory usage
gcloud monitoring time-series list \\
  --filter='metric.type="run.googleapis.com/container/memory/utilizations"'

# Get request latency (p50, p95, p99)
gcloud monitoring time-series list \\
  --filter='metric.type="run.googleapis.com/request_latencies"'
\`\`\`

## 8. Load Test (Concurrent Users)

### Simulate Traffic

\`\`\`bash
# Use Apache Bench
ab -n 1000 -c 50 https://\${DOMAIN}/api/health

# Or Artillery for complex scenarios
artillery quick --count 100 --num 10 https://\${DOMAIN}

# Or k6 for more advanced testing
k6 run load-test.js
\`\`\`

**Measure**:
- Requests per second (RPS)
- Response time under load
- Error rate
- Resource saturation point

**Results Example**:
\`\`\`
Concurrency: 50 users
RPS: 120 req/sec
Avg Response: 250ms
p95 Response: 450ms
p99 Response: 850ms
Error rate: 0.5%
\`\`\`

## 9. Performance Score

\`\`\`javascript
function calculatePerformanceScore(metrics) {
  let score = 100;

  // CPU usage (target: <70%)
  if (metrics.cpu > 90) score -= 20;
  else if (metrics.cpu > 70) score -= 10;

  // Memory usage (target: <80%)
  if (metrics.memory > 95) score -= 20;
  else if (metrics.memory > 80) score -= 10;

  // Response time (target: <200ms)
  if (metrics.responseTime > 500) score -= 15;
  else if (metrics.responseTime > 200) score -= 10;

  // Database queries (target: <100ms)
  if (metrics.dbQueryTime > 200) score -= 15;
  else if (metrics.dbQueryTime > 100) score -= 10;

  // LCP (target: <2.5s)
  if (metrics.lcp > 4.0) score -= 15;
  else if (metrics.lcp > 2.5) score -= 10;

  // Bundle size (target: <200KB)
  if (metrics.bundleSize > 500) score -= 10;
  else if (metrics.bundleSize > 200) score -= 5;

  return Math.max(0, score);
}

const score = calculatePerformanceScore(\${METRICS});
console.log(\`Performance Score: \${score}/100\`);
\`\`\`

## 10. Generate Performance Report

\`\`\`markdown
# Performance Profile Report

**Service**: \${SERVICE_NAME}
**Date**: \${DATE}
**Duration**: \${DURATION} seconds

## Performance Score: \${SCORE}/100

**Grade**: \${GRADE}
**Status**: \${SCORE >= 80 ? '✅ Good' : '⚠️ Needs Optimization'}

## Metrics Summary

| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| CPU Usage | \${CPU_USAGE}% | <70% | \${CPU_STATUS} |
| Memory Usage | \${MEMORY_USAGE}% | <80% | \${MEMORY_STATUS} |
| API Response (p95) | \${RESPONSE_TIME}ms | <200ms | \${RESPONSE_STATUS} |
| DB Query Time (avg) | \${DB_TIME}ms | <100ms | \${DB_STATUS} |
| LCP | \${LCP}s | <2.5s | \${LCP_STATUS} |
| FID | \${FID}ms | <100ms | \${FID_STATUS} |
| CLS | \${CLS} | <0.1 | \${CLS_STATUS} |
| Bundle Size | \${BUNDLE_SIZE}KB | <200KB | \${BUNDLE_STATUS} |

## Bottlenecks Identified

### Critical (Immediate Action Required)

**1. Slow Database Queries**
- Impact: 60% of response time
- Query: SELECT * FROM users JOIN orders...
- Current: 250ms average
- Target: <100ms
- Fix: Add index on users.email, paginate results

**2. Large Bundle Size**
- Impact: 4.5s initial load time
- Current: 850KB (gzipped: 320KB)
- Target: <200KB (gzipped)
- Fix: Code split by route, remove unused lodash

### High Priority

**3. Memory Leak**
- Impact: Container restarts every 6 hours
- Cause: Unclosed event listeners in WebSocket handler
- Fix: Implement proper cleanup in disconnect handler

**4. N+1 Query Pattern**
- Impact: 15 queries per request
- Location: /api/dashboard endpoint
- Fix: Use JOIN or eager loading

## Optimization Recommendations

**Quick Wins** (< 1 hour):
1. Enable gzip compression (-40% transfer size)
2. Add database index on users.email (-60% query time)
3. Increase Cloud Run memory to 1GB (-30% CPU usage)
Expected impact: +15 performance score

**Medium-term** (1-2 days):
1. Implement Redis caching for frequent queries
2. Code split frontend bundle by route
3. Optimize images (use WebP, lazy load)
Expected impact: +20 performance score

**Long-term** (1-2 weeks):
1. Database query optimization and denormalization
2. Implement CDN for static assets
3. Migrate to HTTP/2 server push
Expected impact: +10 performance score

## Resource Utilization

**Current**:
- CPU: \${CPU_USAGE}% average, \${CPU_PEAK}% peak
- Memory: \${MEMORY_USAGE}% average, \${MEMORY_PEAK}% peak
- Network: \${NETWORK_IN}MB in, \${NETWORK_OUT}MB out

**Recommendations**:
${CPU_USAGE > 70 ? '- Increase CPU allocation or optimize code' : '- CPU allocation appropriate'}
${MEMORY_USAGE > 80 ? '- Increase memory or fix memory leaks' : '- Memory allocation appropriate'}

## Load Test Results

**Test Configuration**:
- Virtual users: \${VIRTUAL_USERS}
- Duration: \${TEST_DURATION}
- Target: \${TARGET_RPS} RPS

**Results**:
- Actual RPS: \${ACTUAL_RPS}
- Avg response: \${AVG_RESPONSE}ms
- p95 response: \${P95_RESPONSE}ms
- p99 response: \${P99_RESPONSE}ms
- Error rate: \${ERROR_RATE}%
- Max concurrent: \${MAX_CONCURRENT} users

**Saturation Point**: \${SATURATION_POINT} users (performance degrades after this)

## Next Steps

1. **This Week**:
   - [ ] Add database indexes
   - [ ] Enable compression
   - [ ] Fix memory leak

2. **Next Sprint**:
   - [ ] Implement caching layer
   - [ ] Code split frontend
   - [ ] Optimize images

3. **Ongoing**:
   - [ ] Monthly performance reviews
   - [ ] Monitor Core Web Vitals
   - [ ] Track performance budget

---
**Target Score**: 85/100 (minimum for production)
**Current Score**: \${SCORE}/100
**Gap**: \${85 - SCORE} points

**Re-profile Date**: \${NEXT_PROFILE_DATE}
\`\`\`

Save to: performance-profiles/profile-\${SERVICE_NAME}-\${DATE}.md
  `
})
```

## Usage Examples

```bash
# Profile main application
/performance/profile

# Profile specific service for 5 minutes
/performance/profile --service api-backend --duration 300

# Quick profile (30 seconds)
/performance/profile --duration 30
```

## Integration Points

Auto-runs in:

- `/dev/full-cycle` - Before deployment
- `/devops/deploy` - Pre-deployment check
- `/dev/review` - Performance regression check

## Success Criteria

- ✓ Performance score calculated
- ✓ Bottlenecks identified
- ✓ Optimization recommendations provided
- ✓ Load test results collected
- ✓ Report generated
- ✓ Target: Score >85 for production
- ✓ Core Web Vitals: All green

---
**Uses**: web-performance-optimizer, gcp-monitoring-sre
**Output**: Performance profile report + optimization plan
**Next**: `/performance/optimize` (implement fixes)
**Target**: Performance Score >85/100
