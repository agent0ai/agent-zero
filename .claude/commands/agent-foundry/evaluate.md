---
description: Evaluate agent performance against benchmarks and production criteria
allowed-tools: [Bash, Read, Write, Task]
argument-hint: "<agent-name> [--benchmark <standard|custom>] [--report]"
---

# /agent-foundry/evaluate - Evaluate Agent Performance

Comprehensive evaluation of agent capabilities against production readiness criteria and performance benchmarks.

## Overview

Evaluation dimensions:

1. **Functional Correctness** - Does it work?
2. **Performance** - How fast?
3. **Quality** - How good are the outputs?
4. **Robustness** - Handles edge cases?
5. **User Experience** - Is it helpful?
6. **Production Readiness** - Safe to deploy?

## Evaluation Process

### Step 1: Functional Correctness

Test all capabilities against ground truth:

```typescript
interface CorrectnessSuite {
  capability: string
  testCases: Array<{
    input: any
    expected: any
    validation: (output: any, expected: any) => boolean
  }>
}

// Example: Database Architect
const correctnessTests = {
  capability: 'design-schema',
  testCases: [
    {
      input: { requirements: "Multi-tenant SaaS" },
      expected: {
        hasOrganizationTable: true,
        allTablesHaveOrgId: true,
        properIndexing: true,
        uuidPrimaryKeys: true
      },
      validation: (output, expected) => {
        return (
          output.tables.includes('organizations') &&
          output.tables.every(t => t.columns.includes('organization_id')) &&
          output.indexes.length >= output.tables.length
        )
      }
    }
  ]
}

// Calculate correctness score
const correctnessScore = testCases.reduce((acc, test) => {
  const output = agent.execute(test.input)
  return acc + (test.validation(output, test.expected) ? 1 : 0)
}, 0) / testCases.length
```

**Correctness Metrics**:

```yaml
functional_correctness:
  overall: 94.7%
  by_capability:
    design-schema: 98%
    optimize-queries: 95%
    create-migrations: 92%
    analyze-performance: 89%

  failure_analysis:
    - capability: analyze-performance
      issue: "Underestimates query complexity for subqueries"
      impact: "Medium"
      fix: "Add subquery depth analysis"
```

### Step 2: Performance Benchmarks

Measure speed and efficiency:

```yaml
performance_benchmarks:
  response_time:
    p50: 1.8s  # Target: <2s ✓
    p95: 4.2s  # Target: <5s ✓
    p99: 9.8s  # Target: <10s ✓

  throughput:
    requests_per_minute: 15  # Target: >10 ✓
    concurrent_requests: 5   # Target: >3 ✓

  resource_usage:
    avg_memory: 287MB  # Target: <512MB ✓
    peak_memory: 445MB
    avg_cpu: 32%       # Target: <50% ✓
    peak_cpu: 68%

  scalability:
    linear_scaling: true
    bottlenecks: "None identified"
```

**Performance Score**: 96% (all targets met, room for optimization)

### Step 3: Output Quality

Evaluate quality dimensions:

```typescript
interface QualityMetrics {
  completeness: number      // 0-100%
  correctness: number       // 0-100%
  clarity: number           // 0-100%
  actionability: number     // 0-100%
  consistency: number       // 0-100%
  professionalism: number   // 0-100%
}

// Automated quality checks
function evaluateOutputQuality(output: any): QualityMetrics {
  return {
    completeness: checkAllRequiredSections(output),
    correctness: validateTechnicalAccuracy(output),
    clarity: assessReadability(output),
    actionability: checkImplementable(output),
    consistency: validateAgainstStandards(output),
    professionalism: checkToneAndFormat(output)
  }
}
```

**Quality Scores**:

```yaml
quality_evaluation:
  completeness: 97%
    - All required sections present
    - Comprehensive examples
    - Complete documentation

  correctness: 93%
    - Technically accurate
    - Follows best practices
    - Some edge cases need work

  clarity: 95%
    - Clear explanations
    - Good code examples
    - Well-structured output

  actionability: 98%
    - Ready-to-use code
    - Clear next steps
    - Implementation guidance

  consistency: 91%
    - Mostly consistent formatting
    - Some variation in style
    - Naming conventions followed

  professionalism: 96%
    - Professional tone
    - Proper terminology
    - Well-formatted

overall_quality_score: 95%
```

### Step 4: Robustness Testing

Test error handling and edge cases:

```yaml
robustness_tests:
  malformed_input:
    test: "Invalid JSON, missing fields, wrong types"
    result: "✓ Graceful error messages"
    score: 100%

  edge_cases:
    test: "Empty input, extreme values, boundary conditions"
    result: "✓ 89% handled correctly"
    issues:
      - "Very large schemas (>100 tables) cause timeout"
      - "Circular dependencies not always detected"
    score: 89%

  error_recovery:
    test: "Retry logic, fallback options, clear error messages"
    result: "✓ Good error recovery"
    score: 94%

  concurrent_access:
    test: "Multiple requests simultaneously"
    result: "✓ No race conditions"
    score: 100%

  long_running_tasks:
    test: "Complex schemas taking >30s"
    result: "⚠ Some timeouts"
    improvement: "Add progress reporting"
    score: 82%

overall_robustness: 93%
```

### Step 5: User Experience Evaluation

Assess from user perspective:

```yaml
ux_evaluation:
  ease_of_use:
    score: 92%
    feedback:
      - "Intuitive command structure"
      - "Clear argument names"
      - "Good defaults"

  helpfulness:
    score: 96%
    feedback:
      - "Solves real problems"
      - "Saves significant time"
      - "Learns from feedback"

  documentation:
    score: 88%
    feedback:
      - "Examples are excellent"
      - "More edge case docs needed"
      - "API reference is clear"

  error_messages:
    score: 94%
    feedback:
      - "Clear and actionable"
      - "Includes fix suggestions"
      - "Good context provided"

  responsiveness:
    score: 91%
    feedback:
      - "Usually fast enough"
      - "Some complex queries slow"
      - "Progress indication needed"

overall_ux_score: 92%
```

### Step 6: Production Readiness

Assess deployment readiness:

```yaml
production_readiness:
  security:
    score: 98%
    checks:
      - ✓ Input sanitization
      - ✓ SQL injection prevention
      - ✓ No secret logging
      - ✓ Audit trail
      - ⚠ Rate limiting (recommended)

  reliability:
    score: 95%
    checks:
      - ✓ Error handling
      - ✓ Graceful degradation
      - ✓ Retry logic
      - ✓ Circuit breakers
      - ✓ Health checks

  observability:
    score: 87%
    checks:
      - ✓ Structured logging
      - ✓ Metrics collection
      - ⚠ Distributed tracing (partial)
      - ✓ Error tracking
      - ⚠ Performance monitoring (basic)

  scalability:
    score: 91%
    checks:
      - ✓ Stateless design
      - ✓ Horizontal scaling
      - ✓ Resource limits
      - ⚠ Caching strategy (basic)
      - ✓ Database pooling

  maintainability:
    score: 93%
    checks:
      - ✓ Clear code structure
      - ✓ Comprehensive tests
      - ✓ Good documentation
      - ✓ Version control
      - ✓ Deployment automation

overall_production_readiness: 93%
```

### Step 7: Comparative Benchmarks

Compare against industry standards:

```yaml
competitive_analysis:
  database_architect:
    vs_manual_design:
      time_savings: 85%
      quality_improvement: 40%
      consistency: 95%

    vs_other_tools:
      prisma_migrations: "More flexible, less opinionated"
      hasura: "Better for custom schemas"
      supabase: "More control, harder to use"

    unique_strengths:
      - Multi-tenant aware by default
      - Performance optimization built-in
      - Migration safety checks
      - Best practices enforcement
```

### Step 8: Evaluation Report

Generate comprehensive report:

```markdown
# Evaluation Report: {agent-name}

## Executive Summary

**Overall Score**: 94.2% (A)

**Production Ready**: ✓ YES
**Recommended Action**: Proceed to grading and beta deployment

### Score Breakdown

| Dimension | Score | Grade | Status |
|-----------|-------|-------|--------|
| Functional Correctness | 94.7% | A | ✓ |
| Performance | 96.0% | A | ✓ |
| Output Quality | 95.0% | A | ✓ |
| Robustness | 93.0% | A | ✓ |
| User Experience | 92.0% | A- | ✓ |
| Production Readiness | 93.0% | A | ✓ |

## Detailed Analysis

### Strengths
1. **Excellent Functional Correctness** (94.7%)
   - All core capabilities working well
   - High accuracy on typical scenarios
   - Good handling of complex requirements

2. **Strong Performance** (96%)
   - Meets all latency targets
   - Good resource utilization
   - Scales well

3. **High Quality Outputs** (95%)
   - Complete and actionable
   - Technically sound
   - Well-documented

### Areas for Improvement

1. **Edge Case Handling** (89%)
   - Large schemas (>100 tables) timeout
   - Circular dependency detection needs work
   - **Impact**: Medium
   - **Fix**: Add complexity analysis and warnings

2. **Observability** (87%)
   - Distributed tracing incomplete
   - Performance monitoring basic
   - **Impact**: Low
   - **Fix**: Enhance instrumentation

3. **Long-Running Tasks** (82%)
   - No progress reporting
   - Some timeouts
   - **Impact**: Medium
   - **Fix**: Add streaming responses

## Competitive Position

**vs Manual Work**: 85% time savings, 40% quality improvement
**vs Other Tools**: More flexible, better multi-tenant support
**Unique Value**: Built-in best practices, production-ready migrations

## Recommendation

**PROCEED TO GRADING**

Agent demonstrates:
✓ Production-quality performance
✓ High user satisfaction potential
✓ Competitive advantages
✓ Manageable improvement areas

Next Steps:
1. Run: /agent-foundry/grade {agent-name}
2. Address medium-priority improvements
3. Prepare for beta deployment

## Risk Assessment

**Low Risk** - No critical issues identified
- Minor improvements needed
- Well within production standards
- Good error handling and recovery
```

## Evaluation Suites

### Suite 1: Quick Eval (15 min)

Essential metrics only

### Suite 2: Standard Eval (1 hour)

All dimensions, standard benchmarks

### Suite 3: Comprehensive Eval (3 hours)

Full analysis including competitive benchmarks

## Usage Examples

### Example 1: Standard Evaluation

```bash
/agent-foundry/evaluate database-architect --benchmark standard --report
```

Produces comprehensive evaluation report.

### Example 2: Custom Benchmarks

```bash
/agent-foundry/evaluate security-auditor --benchmark custom --config ./benchmarks.yml
```

Uses custom performance and quality criteria.

### Example 3: Quick Check

```bash
/agent-foundry/evaluate cost-optimizer
```

Fast evaluation of key metrics.

## Quality Gates

To proceed to grading:

✅ Overall score ≥90%
✅ No dimension <85%
✅ All critical tests passing
✅ Performance targets met
✅ No security issues
✅ Production readiness ≥90%

## Troubleshooting

### Issue: Low correctness score

**Solution**: Review failed test cases, retrain on those scenarios

### Issue: Performance below targets

**Solution**: Profile slow operations, optimize critical paths

### Issue: Poor UX score

**Solution**: Collect user feedback, improve documentation and error messages

### Issue: Production readiness concerns

**Solution**: Address security, reliability, or observability gaps
