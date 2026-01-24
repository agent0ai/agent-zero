---
description: Review architecture for scalability, security, maintainability, and best practices with actionable recommendations
argument-hint: "[--focus <scalability|security|maintainability|performance|cost|all>] [--depth <quick|thorough|comprehensive>] [--format <checklist|report|scorecard>]"
allowed-tools: [Read, Write, Bash, Glob, Grep, WebSearch, AskUserQuestion]
---

# Architecture Review Command

## What This Command Does

This command performs comprehensive architecture audits by:

- Analyzing system design against industry best practices
- Evaluating scalability, security, maintainability, performance
- Identifying technical debt and architectural risks
- Scoring architecture maturity across multiple dimensions
- Providing prioritized recommendations for improvement
- Comparing against well-architected frameworks (AWS, Azure, Google Cloud)

The review produces actionable findings with business impact and remediation effort estimates.

## Usage Examples

### Full Architecture Review

```bash
/architecture:review
```

Interactive comprehensive review covering all dimensions.

### Quick Security Review

```bash
/architecture:review --focus security --depth quick
```

Fast security-focused review with critical findings only.

### Scalability Deep Dive

```bash
/architecture:review --focus scalability --depth thorough
```

Thorough analysis of scalability patterns and bottlenecks.

### Cost Optimization Review

```bash
/architecture:review --focus cost --depth comprehensive
```

Comprehensive cost analysis with optimization recommendations.

### Scorecard Format

```bash
/architecture:review --format scorecard
```

Generate numerical scores across all architecture dimensions.

## Review Dimensions

### 1. Scalability

**Evaluates**: Ability to handle growth in users, data, and traffic

**Key Areas**:

- **Horizontal Scaling**: Can you add more instances?
- **Vertical Scaling**: What are the upper limits?
- **Data Partitioning**: Sharding, replication strategies
- **Caching**: Multi-level cache hierarchy
- **Load Balancing**: Distribution strategies
- **Database Scaling**: Read replicas, connection pooling
- **Stateless Design**: Session management, shared state

**Red Flags**:

- Single point of failure (SPOF)
- Monolithic database without sharding plan
- In-memory state without distributed cache
- No load balancing strategy
- Hardcoded limits on resources

**Best Practices**:

- Stateless application tier
- Read replicas for read-heavy workloads
- CDN for static assets
- Message queues for async processing
- Auto-scaling policies defined

### 2. Security

**Evaluates**: Protection against threats and compliance posture

**Key Areas**:

- **Authentication**: Multi-factor, session management
- **Authorization**: RBAC, ABAC, least privilege
- **Data Encryption**: At rest, in transit, key management
- **Network Security**: VPC, firewalls, WAF, DDoS protection
- **Secrets Management**: No hardcoded secrets, vault usage
- **API Security**: Rate limiting, input validation, CORS
- **Compliance**: HIPAA, PCI-DSS, GDPR, SOC2
- **Vulnerability Management**: Patching, dependency scanning
- **Audit Logging**: Comprehensive audit trails

**Red Flags**:

- Secrets in code or environment variables
- No encryption at rest for sensitive data
- Missing authentication on internal APIs
- Overly permissive IAM roles
- No rate limiting on public endpoints
- Lack of audit logging

**Best Practices**:

- Principle of least privilege
- Secrets in dedicated secret manager
- TLS 1.3 for all traffic
- WAF in front of public APIs
- Regular security audits and pen tests
- Automated vulnerability scanning

### 3. Maintainability

**Evaluates**: Ease of modification, debugging, and evolution

**Key Areas**:

- **Code Organization**: Clear modules, separation of concerns
- **Documentation**: Architecture diagrams, ADRs, runbooks
- **Testing**: Unit, integration, E2E coverage
- **Observability**: Logging, metrics, tracing, alerting
- **Dependency Management**: Up-to-date, minimal dependencies
- **Technical Debt**: Tracked and prioritized
- **Standards**: Consistent coding, naming, structure

**Red Flags**:

- No architecture documentation
- Test coverage <60%
- No centralized logging
- Unclear deployment process
- Inconsistent code standards
- Tight coupling between components

**Best Practices**:

- C4 diagrams for architecture
- ADRs for major decisions
- 80%+ test coverage
- Centralized logging and metrics
- Automated code quality checks
- Clear component boundaries

### 4. Performance

**Evaluates**: Speed, throughput, and resource efficiency

**Key Areas**:

- **Response Time**: P50, P95, P99 latency targets
- **Throughput**: Requests per second capacity
- **Database Performance**: Query optimization, indexing
- **Caching Strategy**: Cache hit ratios, TTLs
- **Asset Optimization**: Compression, minification, lazy loading
- **API Efficiency**: N+1 query prevention, batching
- **Resource Utilization**: CPU, memory, disk, network

**Red Flags**:

- No performance budgets defined
- Missing database indexes
- No caching layer
- Synchronous processing of heavy tasks
- No CDN for static assets
- API response times >500ms

**Best Practices**:

- P95 latency <200ms for API calls
- Multi-level caching (CDN, app, database)
- Database query optimization
- Async processing for heavy tasks
- Performance monitoring and alerting
- Regular load testing

### 5. Reliability & Availability

**Evaluates**: Uptime, fault tolerance, disaster recovery

**Key Areas**:

- **Redundancy**: Multi-AZ, multi-region deployment
- **Fault Tolerance**: Graceful degradation, circuit breakers
- **Disaster Recovery**: Backup strategy, RTO/RPO defined
- **Health Checks**: Liveness and readiness probes
- **Error Handling**: Retries, exponential backoff, dead letter queues
- **SLA Definition**: Uptime targets and monitoring

**Red Flags**:

- Single availability zone deployment
- No backup strategy
- No health checks configured
- Missing circuit breakers
- Undefined RTO/RPO
- No chaos engineering

**Best Practices**:

- Multi-AZ deployment for critical services
- Automated backups with tested restore
- Circuit breakers for external dependencies
- Comprehensive health checks
- RTO <4 hours, RPO <1 hour
- Regular disaster recovery drills

### 6. Cost Optimization

**Evaluates**: Resource efficiency and cost-effectiveness

**Key Areas**:

- **Right-Sizing**: Appropriate instance sizes
- **Reserved Capacity**: Commitments for predictable workloads
- **Auto-Scaling**: Scale down during low traffic
- **Storage Optimization**: Tiering, lifecycle policies
- **Cost Monitoring**: Budgets, alerts, attribution
- **Waste Elimination**: Unused resources, zombie instances

**Red Flags**:

- Over-provisioned instances (low utilization)
- No auto-scaling configured
- Unused resources running 24/7
- No cost monitoring or budgets
- Using on-demand for steady-state workloads

**Best Practices**:

- Reserved instances for baseline load
- Auto-scaling for variable load
- Storage tiering (hot/warm/cold)
- Regular cost reviews
- Cost allocation tags
- Cleanup automation

### 7. Operational Excellence

**Evaluates**: Operations, monitoring, incident response

**Key Areas**:

- **Monitoring**: Comprehensive metrics and dashboards
- **Alerting**: Proactive alerts on key metrics
- **Incident Response**: Runbooks, on-call rotation
- **CI/CD**: Automated pipelines, deployment safety
- **Infrastructure as Code**: Terraform, CloudFormation
- **Rollback Strategy**: Quick rollback capability

**Red Flags**:

- Manual deployment processes
- No production monitoring
- Missing runbooks
- No rollback capability
- Unclear on-call process

**Best Practices**:

- Automated CI/CD pipelines
- 100% infrastructure as code
- Comprehensive dashboards
- Runbooks for common incidents
- Automated rollback on failure
- Post-incident reviews (blameless)

## Review Output Formats

### 1. Checklist Format

```markdown
# Architecture Review Checklist

## Scalability
- [x] Stateless application tier
- [x] Load balancer configured
- [ ] Database read replicas (MISSING)
- [x] Auto-scaling policies defined
- [ ] Caching strategy implemented (PARTIAL)

**Score**: 3/5 (60%)
**Priority Gaps**: Database scaling, comprehensive caching

## Security
- [x] Authentication with JWT
- [ ] Multi-factor authentication (MISSING)
- [x] HTTPS everywhere
- [ ] Secrets in vault (USING ENV VARS)
- [x] Rate limiting on APIs
- [ ] WAF configured (MISSING)

**Score**: 3/6 (50%)
**Critical Gaps**: MFA, secrets management, WAF

[Additional sections...]
```

### 2. Report Format

```markdown
# Architecture Review Report
**Date**: 2025-01-15
**System**: E-commerce Platform
**Reviewer**: Claude Architecture Agent
**Review Type**: Comprehensive

## Executive Summary

Overall Architecture Maturity: **Level 3 (Defined)**

The architecture demonstrates solid fundamentals with good scalability and security practices. Key gaps include disaster recovery planning, comprehensive observability, and cost optimization. Recommended focus areas:

1. **Critical**: Implement secrets management (Vault/AWS Secrets Manager)
2. **High**: Add multi-region disaster recovery
3. **Medium**: Enhance observability with distributed tracing

**Total Findings**: 23 (4 Critical, 8 High, 7 Medium, 4 Low)

## Dimension Scores

| Dimension | Score | Level | Trend |
|-----------|-------|-------|-------|
| Scalability | 7/10 | Good | ↑ Improving |
| Security | 6/10 | Fair | → Stable |
| Maintainability | 8/10 | Good | ↑ Improving |
| Performance | 7/10 | Good | → Stable |
| Reliability | 5/10 | Fair | ↓ Needs Attention |
| Cost Optimization | 4/10 | Poor | ↓ Needs Attention |
| Operational Excellence | 6/10 | Fair | ↑ Improving |

**Overall**: 6.1/10 (Fair - Needs Improvement)

## Critical Findings

### Finding #1: Secrets in Environment Variables (CRITICAL)
**Dimension**: Security
**Risk**: High - Credentials exposed in container orchestration
**Impact**: Potential data breach, compliance violations

**Current State**:
- Database credentials stored in Kubernetes secrets (base64 encoded)
- API keys in environment variables
- No rotation policy

**Recommended Solution**:
- Implement HashiCorp Vault or AWS Secrets Manager
- Use dynamic secrets with short TTLs
- Implement automatic rotation
- Audit all secret access

**Effort**: 2-3 weeks
**Cost**: $200-500/month (Vault hosting)
**Priority**: P0 (Immediate)

### Finding #2: No Multi-Region Disaster Recovery (CRITICAL)
**Dimension**: Reliability
**Risk**: High - Complete service outage if region fails
**Impact**: 24+ hour RTO, potential data loss

**Current State**:
- Single region deployment (us-east-1)
- Database backups to same region
- No failover plan

**Recommended Solution**:
- Deploy standby environment in us-west-2
- Configure cross-region database replication
- Implement DNS-based failover (Route53)
- Document DR runbook and test quarterly

**Effort**: 4-6 weeks
**Cost**: +60% infrastructure (standby region)
**Priority**: P0 (Within 3 months)

[Additional findings...]

## Recommendations by Priority

### Immediate (P0) - Next 30 Days
1. Implement secrets management solution
2. Add WAF in front of public APIs
3. Enable MFA for admin accounts
4. Set up cost monitoring and budgets

### High Priority (P1) - Next 90 Days
1. Multi-region disaster recovery
2. Implement distributed tracing
3. Add database read replicas
4. Right-size over-provisioned instances

### Medium Priority (P2) - Next 6 Months
1. Enhance test coverage to 80%+
2. Implement chaos engineering
3. Add comprehensive API documentation
4. Create C4 architecture diagrams

### Low Priority (P3) - Next 12 Months
1. Evaluate migration to serverless for async tasks
2. Implement GraphQL layer
3. Add machine learning for fraud detection
4. Optimize database with partitioning

## Cost-Benefit Analysis

| Improvement | Effort | Cost | Savings/Benefit | ROI |
|-------------|--------|------|-----------------|-----|
| Right-size instances | 1 week | $0 | $2,400/year | ∞ |
| Auto-scaling | 2 weeks | $0 | $3,600/year | ∞ |
| Secrets management | 3 weeks | $6,000/year | Risk mitigation | High |
| DR setup | 6 weeks | +$30K/year | Business continuity | Medium |
| Distributed tracing | 2 weeks | $1,200/year | Faster debugging | High |

## Next Steps

1. **Week 1**: Prioritize findings with stakeholders
2. **Week 2-4**: Implement P0 items (secrets, WAF, MFA)
3. **Month 2-3**: Plan and execute DR setup
4. **Month 4-6**: Address P1 and P2 items
5. **Month 6**: Schedule follow-up architecture review

## Appendix

- [A] Detailed security audit findings
- [B] Performance benchmarks and bottlenecks
- [C] Cost analysis breakdown
- [D] Recommended architecture diagrams
```

### 3. Scorecard Format

```markdown
# Architecture Scorecard

**System**: E-commerce Platform
**Date**: 2025-01-15
**Overall Maturity**: Level 3 - Defined (6.1/10)

## Maturity Levels

1. **Initial** (1-2): Ad-hoc processes, reactive
2. **Repeatable** (3-4): Some standards, inconsistent
3. **Defined** (5-6): Documented processes, mostly consistent
4. **Managed** (7-8): Quantitatively measured and controlled
5. **Optimizing** (9-10): Continuous improvement, industry-leading

## Dimension Scores

### Scalability: 7.0/10 (Good)
- Horizontal Scaling: 8/10 ✓
- Vertical Scaling: 6/10 ~
- Data Partitioning: 5/10 ~
- Caching: 7/10 ✓
- Load Balancing: 9/10 ✓
- Database Scaling: 6/10 ~
- Stateless Design: 8/10 ✓

**Strengths**: Auto-scaling, load balancing
**Gaps**: Database sharding, cache hierarchy

### Security: 6.0/10 (Fair)
- Authentication: 7/10 ✓
- Authorization: 7/10 ✓
- Encryption: 6/10 ~
- Network Security: 5/10 ~
- Secrets Management: 3/10 ✗
- API Security: 8/10 ✓
- Compliance: 5/10 ~
- Audit Logging: 6/10 ~

**Strengths**: Strong auth, API security
**Gaps**: Secrets management, WAF, compliance

### Maintainability: 8.0/10 (Good)
- Code Organization: 8/10 ✓
- Documentation: 7/10 ✓
- Testing: 7/10 ✓
- Observability: 6/10 ~
- Dependency Mgmt: 9/10 ✓
- Technical Debt: 8/10 ✓
- Standards: 9/10 ✓

**Strengths**: Clean code, good tests, standards
**Gaps**: Observability, architecture diagrams

[Additional dimensions...]

## Radar Chart Visualization

```

       Scalability (7)
              ⬆
              |
Cost (4) ←----+----→ Security (6)
              |
              |
       Reliability (5)

         Performance (7)

```

## Priority Matrix

```

High Impact
    ↑
    |  [Secrets Mgmt]     [Multi-Region DR]
    |  [WAF]              [Observability]
    |
    |  [Cost Optimization][Test Coverage]
    |  [API Docs]         [Chaos Eng]
    |
    └───────────────────────────────→
         Low Effort          High Effort

```

## Benchmarking

| Metric | This System | Industry P50 | Industry P90 | Target |
|--------|-------------|--------------|--------------|--------|
| Test Coverage | 65% | 70% | 85% | 80% |
| Deployment Frequency | Weekly | Daily | Multiple/day | Daily |
| Mean Time to Recovery | 4 hours | 1 hour | 15 min | 1 hour |
| Change Failure Rate | 15% | 10% | 5% | 10% |
| Security Vulnerabilities | 23 | 15 | 5 | 10 |

## Recommendations Summary

**Total**: 23 findings
- **Critical (P0)**: 4 findings - Address in 30 days
- **High (P1)**: 8 findings - Address in 90 days
- **Medium (P2)**: 7 findings - Address in 6 months
- **Low (P3)**: 4 findings - Address in 12 months

**Estimated Total Effort**: 32 weeks
**Estimated Total Cost**: $45,000 (one-time) + $12,000/year (recurring)
**Expected ROI**: $60,000/year in savings + risk mitigation
```

## Business Value & ROI

### Risk Mitigation

- **Problem**: Unknown security vulnerabilities and architectural weaknesses
- **Solution**: Systematic architecture review identifies and prioritizes risks
- **ROI**: Avoid one security breach ($4M average cost) = infinite ROI

### Cost Savings

- **Problem**: Over-provisioned resources and inefficient architecture
- **Solution**: Cost optimization review finds 20-40% savings
- **ROI**: $50K-$200K annual savings for typical mid-size system

### Faster Delivery

- **Problem**: Technical debt and complexity slow down development
- **Solution**: Maintainability review identifies blockers
- **ROI**: 30% faster feature delivery = more revenue, lower costs

### Better Reliability

- **Problem**: Downtime costs revenue and customer trust
- **Solution**: Reliability review prevents outages
- **ROI**: 99.9% vs 99% uptime = $X saved (calculate based on revenue/hour)

### Informed Roadmap

- **Problem**: Unclear what to prioritize in architecture improvements
- **Solution**: Review provides prioritized roadmap with effort/impact
- **ROI**: Efficient allocation of engineering resources

## Success Metrics

### Review Quality Checklist

- [ ] All 7 dimensions evaluated (scalability, security, maintainability, performance, reliability, cost, operations)
- [ ] Findings include current state, recommended solution, effort, and priority
- [ ] Scores compared against industry benchmarks
- [ ] Prioritization based on business impact, not just technical severity
- [ ] Cost-benefit analysis included for major recommendations
- [ ] Actionable roadmap with timelines
- [ ] Executive summary for non-technical stakeholders

### Review Completeness

- [ ] Codebase analyzed (structure, dependencies, patterns)
- [ ] Infrastructure reviewed (IaC, deployment, monitoring)
- [ ] Documentation examined (architecture diagrams, ADRs, runbooks)
- [ ] Metrics collected (performance, cost, reliability)
- [ ] Stakeholder interviews conducted (if applicable)
- [ ] Industry best practices referenced

### Follow-Up Actions

- [ ] Findings presented to stakeholders
- [ ] Priority and timeline agreed upon
- [ ] Owners assigned to each finding
- [ ] Tracking system updated (Jira, Linear, etc.)
- [ ] Follow-up review scheduled
- [ ] Progress tracked against recommendations

## Execution Protocol

### Quick Review (30-45 minutes)

1. **Scan codebase** (10 min) - Structure, patterns, organization
2. **Check security** (10 min) - Secrets, auth, encryption
3. **Review infrastructure** (10 min) - Deployment, scaling, monitoring
4. **Generate findings** (10 min) - Top 5-10 critical issues
5. **Create checklist** (5 min) - Prioritized action items

**Output**: Checklist format with top findings

### Thorough Review (2-3 hours)

1. **Analyze all dimensions** (60 min) - Score each dimension
2. **Benchmark** (20 min) - Compare to industry standards
3. **Prioritize findings** (20 min) - Impact vs effort matrix
4. **Cost-benefit analysis** (20 min) - ROI for major changes
5. **Create report** (30 min) - Comprehensive findings document

**Output**: Full report with scores, findings, roadmap

### Comprehensive Review (1-2 days)

1. **Deep codebase analysis** (4 hours) - All files, patterns, debt
2. **Infrastructure audit** (3 hours) - IaC, configs, cloud resources
3. **Documentation review** (2 hours) - Diagrams, ADRs, runbooks
4. **Stakeholder interviews** (2 hours) - Pain points, goals
5. **Benchmarking** (1 hour) - Industry comparison
6. **Finding generation** (3 hours) - Detailed findings with solutions
7. **Roadmap creation** (2 hours) - Prioritized, timelined plan
8. **Report writing** (3 hours) - Executive summary, technical details

**Output**: Comprehensive scorecard, report, and presentation

## Integration with Other Commands

- **Architecture Design**: Use `/architecture:design` to create architecture, then `/architecture:review` to audit
- **ADR Creation**: Reference review findings in ADRs when making improvements
- **Diagrams**: Use `/architecture:diagram` to document current and future state
- **Implementation**: Use `/dev:feature-request` to break down remediation into stories

---

**Best Practices**:

1. Review architecture every 6-12 months
2. Review before major changes or migrations
3. Review after significant growth or incidents
4. Involve multiple stakeholders in review
5. Focus on business impact, not just technical perfection
6. Create actionable roadmap, not just a report
7. Track progress on recommendations over time
