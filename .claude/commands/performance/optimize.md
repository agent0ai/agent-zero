---
description: Get AI-powered performance optimization recommendations
argument-hint: [--profile-report <file>]
model: claude-sonnet-4-5-20250929
allowed-tools: Task, Read, Write
---

Performance optimization recommendations: **${ARGUMENTS}**

## AI-Powered Optimization

**Analyzes**:

- Performance profile data
- Code patterns
- Infrastructure configuration
- Best practices

Routes to **web-performance-optimizer**:

```javascript
await Task({
  subagent_type: 'web-performance-optimizer',
  description: 'Generate optimization recommendations',
  prompt: `Generate performance optimization recommendations.

${PROFILE_REPORT ? 'Based on profile report: ' + PROFILE_REPORT : 'Analyzing current codebase'}

Provide actionable optimization recommendations:

## 1. Analyze Performance Data

Read performance metrics from:
- Latest performance profile report
- GCP Cloud Monitoring metrics
- Lighthouse reports
- Load test results

Identify top bottlenecks ranked by impact.

## 2. Code-Level Optimizations

### Database Queries

**Issue**: N+1 queries, missing indexes, full table scans
**Solution**:
\`\`\`javascript
// Before (N+1 query)
const users = await User.findAll();
for (const user of users) {
  user.orders = await Order.findAll({ where: { userId: user.id } });
}

// After (eager loading)
const users = await User.findAll({
  include: [{ model: Order }]
});
\`\`\`

### Caching Layer

**Issue**: Repeated database queries for same data
**Solution**: Implement Redis caching
\`\`\`javascript
// Add caching middleware
const cache = require('./cache');

app.get('/api/products', async (req, res) => {
  const cacheKey = 'products:all';
  const cached = await cache.get(cacheKey);
  if (cached) return res.json(cached);

  const products = await Product.findAll();
  await cache.set(cacheKey, products, 300); // 5 min TTL
  res.json(products);
});
\`\`\`

### Async Processing

**Issue**: Blocking operations in request handler
**Solution**: Move to background jobs
\`\`\`javascript
// Before (blocking)
app.post('/api/report', async (req, res) => {
  const report = await generateReport(req.body); // Takes 10 seconds
  await sendEmail(report); // Takes 2 seconds
  res.json({ success: true });
});

// After (async)
app.post('/api/report', async (req, res) => {
  const jobId = await queue.add('generate-report', req.body);
  res.json({ jobId, status: 'processing' });
});
\`\`\`

## 3. Frontend Optimizations

### Code Splitting

\`\`\`javascript
// Before (all in one bundle)
import Dashboard from './pages/Dashboard';
import Reports from './pages/Reports';
import Settings from './pages/Settings';

// After (lazy loading)
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Reports = lazy(() => import('./pages/Reports'));
const Settings = lazy(() => import('./pages/Settings'));
\`\`\`

### Image Optimization

\`\`\`html
<!-- Before -->
<img src="hero.jpg" width="1200" height="800" />

<!-- After -->
<picture>
  <source srcset="hero.webp" type="image/webp" />
  <img src="hero.jpg" loading="lazy" width="1200" height="800" alt="Hero" />
</picture>
\`\`\`

### Remove Unused Dependencies

\`\`\`bash
# Analyze bundle
npx webpack-bundle-analyzer

# Remove unused packages
npm uninstall lodash
npm install lodash.debounce # Install only what you need
\`\`\`

## 4. Infrastructure Optimizations

### Cloud Run Scaling

\`\`\`bash
# Adjust Cloud Run configuration for better performance
gcloud run services update \${SERVICE} \\
  --min-instances=1 \\ # Avoid cold starts
  --max-instances=10 \\
  --concurrency=80 \\ # Adjust based on profiling
  --cpu=2 \\ # Increase if CPU-bound
  --memory=2Gi # Increase if memory-bound
\`\`\`

### Database Connection Pooling

\`\`\`javascript
// Configure connection pool
const pool = new Pool({
  max: 20, // Max connections
  min: 5, // Min connections
  idleTimeoutMillis: 30000
});
\`\`\`

### CDN Configuration

\`\`\`bash
# Enable Cloud CDN
gcloud compute backend-services update \${SERVICE} \\
  --enable-cdn \\
  --cache-mode=CACHE_ALL_STATIC \\
  --default-ttl=3600
\`\`\`

## 5. Generate Optimization Plan

\`\`\`markdown
# Performance Optimization Plan

**Current Performance Score**: \${CURRENT_SCORE}/100
**Target Performance Score**: 90/100
**Expected Improvement**: +\${IMPROVEMENT} points

## Priority 1: Critical (Do This Week)

### Optimization 1: Add Database Indexes
**Current Impact**: 60% of response time spent on slow queries
**Expected Improvement**: -150ms response time (-60%)
**Effort**: 2 hours
**Implementation**:
\`\`\`sql
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_orders_user_id ON orders(user_id);
\`\`\`

### Optimization 2: Enable Compression
**Current Impact**: 2.5MB transferred per page load
**Expected Improvement**: -1.5MB transfer size (-60%)
**Effort**: 30 minutes
**Implementation**:
\`\`\`javascript
app.use(compression({ level: 6 }));
\`\`\`

### Optimization 3: Fix Memory Leak
**Current Impact**: Service restarts every 6 hours
**Expected Improvement**: Zero restarts
**Effort**: 4 hours
**Implementation**: Clean up event listeners in WebSocket disconnect handler

**Total Expected Impact**: +25 performance score

## Priority 2: High (Next Sprint)

### Optimization 4: Implement Redis Caching
**Expected Improvement**: +15 performance score
**Effort**: 1 day

### Optimization 5: Code Split Frontend
**Expected Improvement**: +10 performance score
**Effort**: 2 days

### Optimization 6: Optimize Images
**Expected Improvement**: +8 performance score
**Effort**: 4 hours

**Total Expected Impact**: +33 performance score

## Priority 3: Medium (Nice to Have)

### Optimization 7: Database Denormalization
**Expected Improvement**: +5 performance score
**Effort**: 3 days

### Optimization 8: HTTP/2 Server Push
**Expected Improvement**: +3 performance score
**Effort**: 1 day

## Implementation Timeline

**Week 1**: Priority 1 optimizations (Critical)
- Expected score after week 1: \${CURRENT_SCORE + 25}

**Week 2-3**: Priority 2 optimizations (High)
- Expected score after week 3: \${CURRENT_SCORE + 58}

**Week 4+**: Priority 3 optimizations (Medium)
- Final expected score: 90+

## Success Metrics

**Before Optimization**:
- Performance score: \${CURRENT_SCORE}/100
- Response time (p95): \${CURRENT_P95}ms
- LCP: \${CURRENT_LCP}s
- Bundle size: \${CURRENT_BUNDLE}KB

**After Optimization** (projected):
- Performance score: 90/100
- Response time (p95): <200ms
- LCP: <2.0s
- Bundle size: <150KB

## Rollback Plan

For each optimization:
1. Deploy to staging first
2. Run load tests to verify improvement
3. Monitor for 24 hours
4. If performance degrades → rollback
5. If stable → deploy to production

\`\`\`

Save to: performance-optimizations/optimization-plan-\${DATE}.md
  `
})
```

## Usage Examples

```bash
# Generate optimization recommendations
/performance/optimize

# Based on specific profile report
/performance/optimize --profile-report performance-profiles/profile-2024-11-15.md
```

## Output

Provides:

- Prioritized optimization recommendations
- Code examples for fixes
- Expected performance improvement
- Implementation timeline
- Success metrics

## Success Criteria

- ✓ Optimizations prioritized by impact
- ✓ Code examples provided
- ✓ Expected improvements quantified
- ✓ Timeline realistic
- ✓ Target: Reach 90+ performance score

---
**Uses**: web-performance-optimizer
**Output**: Detailed optimization plan with code examples
**Next**: Implement optimizations, re-run `/performance/profile`
