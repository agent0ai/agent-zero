---
description: Deploy certified agent to customer environments with monitoring and rollback
allowed-tools: [Bash, Read, Write, Task, AskUserQuestion]
argument-hint: "<agent-name> [--stage <dev|beta|production>] [--customers <list>] [--canary <percentage>]"
---

# /agent-foundry/deploy - Deploy Agent to Customers

Deploy certified agents to customer environments with staged rollout, monitoring, and automatic rollback capabilities.

## Deployment Strategies

### Strategy 1: Development Deploy

- **Target**: Internal testing
- **Users**: Development team
- **Duration**: 1-2 weeks
- **Rollback**: Immediate

### Strategy 2: Beta Deploy

- **Target**: Selected customers
- **Users**: 5-10 beta participants
- **Duration**: 2-4 weeks
- **Rollback**: <1 hour

### Strategy 3: Canary Deploy

- **Target**: Small percentage of users
- **Users**: 5-10% of customer base
- **Duration**: 1-2 weeks
- **Rollback**: Automatic on errors

### Strategy 4: Production Deploy

- **Target**: All customers
- **Users**: Full customer base
- **Duration**: Ongoing
- **Rollback**: <15 minutes

## Deployment Process

### Step 1: Pre-Deployment Validation

Verify deployment readiness:

```yaml
pre_deployment_checklist:
  certification:
    ✓ Agent certified (minimum Silver)
    ✓ Certificate valid
    ✓ No open critical issues
    ✓ Test coverage ≥90%

  infrastructure:
    ✓ Resources provisioned
    ✓ Database migrations ready
    ✓ Configuration verified
    ✓ Secrets rotated

  documentation:
    ✓ User guide published
    ✓ API documentation updated
    ✓ Release notes prepared
    ✓ Support runbook ready

  monitoring:
    ✓ Alerts configured
    ✓ Dashboards created
    ✓ Logging enabled
    ✓ Tracing instrumented

  compliance:
    ✓ Security review passed
    ✓ Privacy assessment done
    ✓ Legal approval obtained
    ✓ SLA documented
```

### Step 2: Customer Selection

For beta/canary deploys, select customers:

```typescript
interface CustomerSelection {
  criteria: {
    representative: boolean      // Diverse use cases
    engaged: boolean             // Active users
    technical: boolean           // Can provide feedback
    lowRisk: boolean            // Not mission-critical
  }

  customers: Array<{
    organizationId: string
    name: string
    tier: 'startup' | 'growth' | 'enterprise'
    usageLevel: 'light' | 'medium' | 'heavy'
    risk: 'low' | 'medium' | 'high'
  }>
}

// Example: Beta deployment
const betaCustomers = selectCustomers({
  count: 10,
  criteria: {
    representative: true,    // Mix of sizes and industries
    engaged: true,          // Active users who give feedback
    technical: true,        // Can debug issues
    lowRisk: true          // Not mission-critical workloads
  }
})
```

### Step 3: Deployment Configuration

Configure deployment parameters:

```yaml
deployment_config:
  agent: "database-architect"
  version: "1.0.0"
  certification: "Gold"

  rollout:
    strategy: "canary"
    percentage: 10        # Start with 10%
    ramp_up: "7 days"    # Increase by 10% every week

  targeting:
    customers:
      - org_id: "abc-123"
        enabled_features: ["design-schema", "optimize-queries"]
      - org_id: "def-456"
        enabled_features: ["all"]

    feature_flags:
      advanced_optimization: false
      experimental_features: false

  resources:
    instances: 3
    memory: "512MB"
    cpu: "0.5"
    auto_scaling:
      min: 2
      max: 10
      target_cpu: 70%

  monitoring:
    health_check_interval: "30s"
    error_threshold: "5%"
    latency_p99: "10s"
    auto_rollback: true
```

### Step 4: Database Migrations

Execute any required migrations:

```bash
# Check migration status
/db/migrate --dry-run --product devflow

# Apply migrations
/db/migrate --product devflow --environment production

# Verify migrations
/db/query --query "SELECT version FROM schema_migrations ORDER BY version DESC LIMIT 1"
```

### Step 5: Deploy Agent

Execute deployment:

```typescript
interface DeploymentSteps {
  1: "Build agent package"
  2: "Push to registry"
  3: "Update configuration"
  4: "Deploy to infrastructure"
  5: "Run smoke tests"
  6: "Enable for selected customers"
  7: "Monitor metrics"
  8: "Collect initial feedback"
}

// Deployment execution
async function deployAgent(config: DeploymentConfig): Promise<DeploymentResult> {
  // 1. Build package
  await buildAgentPackage(config.agent, config.version)

  // 2. Push to registry
  await pushToRegistry(config.agent, config.version)

  // 3. Update configuration in shared services
  await updateAgentConfig(config)

  // 4. Deploy to infrastructure
  const deployment = await deployToInfrastructure({
    agent: config.agent,
    version: config.version,
    instances: config.resources.instances,
    resources: config.resources
  })

  // 5. Health check
  await waitForHealthy(deployment.id, timeout = '5m')

  // 6. Run smoke tests
  const smokeTests = await runSmokeTests(config.agent)
  if (!smokeTests.passed) {
    throw new Error('Smoke tests failed - aborting deployment')
  }

  // 7. Enable for customers
  for (const customer of config.targeting.customers) {
    await enableAgentForCustomer(customer.org_id, config.agent, config.version)
  }

  // 8. Set up monitoring
  await configureMonitoring(config.monitoring)

  return {
    status: 'deployed',
    deploymentId: deployment.id,
    customersEnabled: config.targeting.customers.length,
    timestamp: new Date()
  }
}
```

### Step 6: Monitor Deployment

Track key metrics:

```yaml
monitoring_dashboard:
  health:
    - metric: "Agent availability"
      current: 99.8%
      target: ">99%"
      status: "✓"

    - metric: "Response time (p95)"
      current: "3.2s"
      target: "<5s"
      status: "✓"

  usage:
    - metric: "Requests per minute"
      current: 12
      baseline: 10
      trend: "+20%"

    - metric: "Active users"
      current: 8
      target: 10
      status: "Ramping up"

  errors:
    - metric: "Error rate"
      current: "2.3%"
      target: "<5%"
      status: "✓"

    - metric: "Critical errors"
      current: 0
      target: 0
      status: "✓"

  user_feedback:
    - metric: "User rating"
      current: "8.7/10"
      baseline: "8.0/10"
      trend: "+9%"

    - metric: "Issue reports"
      current: 3
      critical: 0
      status: "✓"
```

### Step 7: Collect Feedback

Gather user feedback:

```typescript
interface UserFeedback {
  organizationId: string
  userId: string
  agentName: string
  rating: number        // 1-10
  capabilities_used: string[]
  feedback: {
    positive: string[]
    issues: string[]
    suggestions: string[]
  }
  wouldRecommend: boolean
}

// Automated feedback collection
async function collectFeedback(deploymentId: string): Promise<FeedbackSummary> {
  const feedback = await getFeedbackForDeployment(deploymentId)

  return {
    totalResponses: feedback.length,
    averageRating: calculateAverage(feedback.map(f => f.rating)),
    nps: calculateNPS(feedback),
    topIssues: extractTopIssues(feedback),
    topPraise: extractTopPraise(feedback),
    recommendationRate: calculateRecommendationRate(feedback)
  }
}
```

### Step 8: Rollout or Rollback

Based on metrics, decide to proceed or rollback:

```yaml
decision_criteria:
  proceed_if:
    - error_rate: "<5%"
    - availability: ">99%"
    - user_rating: ">7.5"
    - critical_issues: 0
    - recommendation_rate: ">70%"

  rollback_if:
    - error_rate: ">10%"
    - availability: "<95%"
    - critical_issues: ">0"
    - user_rating: "<6"
    - recommendation_rate: "<50%"
```

**Auto-Rollback Triggers**:

```typescript
const rollbackTriggers = {
  errorRate: {
    threshold: 10,        // 10% error rate
    window: '5m',         // Over 5 minutes
    action: 'immediate'
  },
  latency: {
    threshold: 15,        // 15s p99
    window: '10m',
    action: 'gradual'     // Reduce traffic first
  },
  availability: {
    threshold: 95,        // <95% availability
    window: '1m',
    action: 'immediate'
  },
  criticalError: {
    threshold: 1,         // Any critical error
    window: 'instant',
    action: 'immediate'
  }
}
```

### Step 9: Deployment Report

Generate deployment summary:

```markdown
# Deployment Report: {agent-name} v{version}

## Deployment Summary

**Status**: ✓ Successful
**Stage**: Beta
**Customers**: 10 organizations
**Deployed**: January 16, 2026 14:30 UTC
**Duration**: 45 minutes

## Deployment Details

| Metric | Value |
|--------|-------|
| Agent | database-architect |
| Version | 1.0.0 |
| Certification | Gold (92.4%) |
| Strategy | Canary (10%) |
| Instances | 3 (auto-scaling 2-10) |
| Resources | 512MB, 0.5 CPU per instance |

## Customer Rollout

| Organization | Status | Enabled Features | Risk Level |
|--------------|--------|------------------|------------|
| TechCorp | ✓ Active | All | Low |
| StartupCo | ✓ Active | Core only | Low |
| Enterprise Inc | ✓ Active | All | Medium |
| ... | ... | ... | ... |

## Performance Metrics (First 24 Hours)

### Health
- **Availability**: 99.8% (target: >99%) ✓
- **Response Time**: p95 3.2s (target: <5s) ✓
- **Error Rate**: 2.3% (target: <5%) ✓
- **Critical Errors**: 0 ✓

### Usage
- **Total Requests**: 1,247
- **Unique Users**: 23
- **Requests/Minute**: 12 avg
- **Most Used Capability**: design-schema (58%)

### User Feedback
- **Rating**: 8.7/10 (baseline: 8.0)
- **NPS**: +45 (promoters: 70%, detractors: 10%)
- **Recommendation Rate**: 85%
- **Issue Reports**: 3 minor, 0 critical

## Issues Detected

### Minor Issues (3)
1. **Progress indication missing**
   - Capability: design-schema
   - Impact: UX (users don't know status)
   - Priority: Low
   - Fix planned: v1.0.1

2. **Large schema timeout**
   - Capability: analyze-performance
   - Impact: Edge case (>100 tables)
   - Priority: Medium
   - Fix planned: v1.1.0

3. **Documentation gap**
   - Area: Advanced examples
   - Impact: Learning curve
   - Priority: Low
   - Fix planned: Documentation update

### No Critical Issues ✓

## User Feedback Highlights

### Positive
- "Saved us 4 hours on schema design"
- "Best practices built-in is amazing"
- "Migration scripts are production-ready"
- "Great multi-tenant support"

### Suggestions
- "Add progress bar for long operations"
- "More examples for complex scenarios"
- "Explain reasoning behind decisions"

## Next Steps

### Immediate (This Week)
- [x] Monitor metrics daily
- [x] Respond to user feedback
- [x] Fix minor issues in v1.0.1

### Short-term (2 Weeks)
- [ ] Expand to 20% of customers
- [ ] Collect comprehensive feedback
- [ ] Prepare v1.1.0 with improvements

### Medium-term (1 Month)
- [ ] Full production rollout
- [ ] Achieve Platinum certification
- [ ] Add advanced features

## Rollback Plan

**Trigger**: Error rate >10% OR critical issue
**Duration**: <15 minutes
**Process**:
1. Disable agent for all customers
2. Route traffic to previous version
3. Investigate issue
4. Fix and redeploy

**Rollback Tested**: ✓ Yes (staging)

## Recommendation

**✓ PROCEED WITH ROLLOUT**

Deployment successful with:
- All metrics within targets
- Positive user feedback
- No critical issues
- Strong recommendation rate

**Next Action**: Expand to 20% after 1 week of stable operation.

## Approval

**Deployed By**: DevOps Team
**Approved By**: Engineering Lead
**Certification**: Gold (valid until April 16, 2026)
**Support Contact**: [email protected]
```

## Deployment Stages

### Stage 1: Development

Internal testing only

### Stage 2: Beta

5-10 selected customers, active monitoring

### Stage 3: Canary

10-25% of customers, gradual rollout

### Stage 4: Production

All customers, full availability

## Usage Examples

### Example 1: Beta Deployment

```bash
/agent-foundry/deploy database-architect --stage beta --customers techcorp,startupco
```

Deploys to specific beta customers.

### Example 2: Canary Deployment

```bash
/agent-foundry/deploy security-auditor --stage production --canary 10
```

Deploys to 10% of all customers.

### Example 3: Full Production

```bash
/agent-foundry/deploy cost-optimizer --stage production
```

Deploys to all customers.

### Example 4: Rollback

```bash
/agent-foundry/deploy database-architect --rollback
```

Rolls back to previous version.

## Deployment Checklist

Pre-deployment:
✅ Agent certified (≥Silver)
✅ Tests passing (≥90%)
✅ Documentation complete
✅ Security review passed
✅ Infrastructure provisioned
✅ Monitoring configured
✅ Rollback plan tested

Post-deployment:
✅ Health checks passing
✅ Metrics within targets
✅ No critical errors
✅ Users notified
✅ Support team briefed
✅ Monitoring active

## Best Practices

1. **Start Small** - Beta first, then canary
2. **Monitor Closely** - Watch metrics hourly initially
3. **Collect Feedback** - Talk to beta users
4. **Be Ready to Rollback** - Have plan and test it
5. **Communicate** - Keep customers informed
6. **Iterate Fast** - Fix issues quickly
7. **Document Everything** - Lessons learned

## Troubleshooting

### Issue: Deployment fails health checks

**Solution**: Check logs, verify configuration, rollback if needed

### Issue: High error rate post-deployment

**Solution**: Investigate errors, disable for affected customers, fix and redeploy

### Issue: Poor user feedback

**Solution**: Collect detailed feedback, plan improvements, communicate timeline

### Issue: Performance degradation

**Solution**: Scale resources, optimize slow operations, consider canary reduction
