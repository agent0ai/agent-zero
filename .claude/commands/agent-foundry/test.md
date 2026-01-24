---
description: Test agent capabilities with validation scenarios and edge cases
allowed-tools: [Bash, Read, Write, Task]
argument-hint: "<agent-name> [--suite <smoke|integration|comprehensive>] [--coverage]"
---

# /agent-foundry/test - Test Agent Capabilities

Validate agent functionality through automated test suites covering typical and edge case scenarios.

## Overview

Tests agent across:

1. **Unit Tests** - Individual capabilities
2. **Integration Tests** - Multi-step workflows
3. **Performance Tests** - Response time and throughput
4. **Quality Tests** - Output validation
5. **Edge Case Tests** - Boundary conditions and error handling

## Test Suites

### Suite 1: Smoke Tests (Fast)

Quick validation of core functionality

**Duration**: 30-60 seconds
**Tests**: 5-10 critical paths

```yaml
smoke_tests:
  - capability_availability
  - basic_input_validation
  - simple_execution
  - output_format_check
  - error_handling_basic
```

### Suite 2: Integration Tests (Standard)

Multi-capability workflows

**Duration**: 5-10 minutes
**Tests**: 20-30 scenarios

```yaml
integration_tests:
  - multi_step_workflows
  - agent_collaboration
  - tool_usage_patterns
  - state_management
  - context_preservation
  - dependency_resolution
```

### Suite 3: Comprehensive Tests (Thorough)

Full validation including edge cases

**Duration**: 15-30 minutes
**Tests**: 50-100 scenarios

```yaml
comprehensive_tests:
  - all_capabilities
  - edge_cases
  - stress_testing
  - security_validation
  - compliance_checks
  - performance_benchmarks
  - regression_tests
```

## Test Process

### Step 1: Load Test Scenarios

For each agent capability, generate test scenarios:

```typescript
// Example: Database Architect
const testScenarios = [
  {
    capability: 'design-schema',
    scenario: 'Multi-tenant SaaS application',
    input: {
      requirements: 'Users, Organizations, Subscriptions',
      constraints: ['PostgreSQL', 'UUID PKs', 'Multi-tenant']
    },
    expected: {
      tables: ['users', 'organizations', 'subscriptions'],
      isolation: 'organization_id column on all tables',
      indexes: 'Foreign keys and org_id indexed',
      migrations: 'Idempotent SQL scripts'
    }
  },
  {
    capability: 'optimize-queries',
    scenario: 'Slow user lookup query',
    input: {
      query: 'SELECT * FROM users WHERE email = ?',
      performance: 'Current: 250ms, Target: <50ms'
    },
    expected: {
      suggestion: 'Add index on users(email)',
      optimizedQuery: 'Using covering index',
      estimatedImprovement: '>80% faster'
    }
  }
]
```

### Step 2: Execute Tests

Run each test scenario and capture results:

```typescript
interface TestResult {
  scenario: string
  capability: string
  status: 'pass' | 'fail' | 'skip'
  duration: number
  output: any
  validations: Array<{
    check: string
    passed: boolean
    message?: string
  }>
  errors?: string[]
}
```

### Step 3: Validate Outputs

For each test, validate:

**Structure Validation**:

```typescript
✓ Output has all required sections
✓ Format matches specification
✓ No missing fields
✓ Data types correct
```

**Content Validation**:

```typescript
✓ Solutions are appropriate
✓ Recommendations are sound
✓ Examples are relevant
✓ Documentation is clear
```

**Quality Validation**:

```typescript
✓ Meets quality standards
✓ Follows best practices
✓ Passes compliance checks
✓ Achieves performance targets
```

### Step 4: Performance Benchmarks

Measure agent performance:

```yaml
performance_metrics:
  response_time:
    p50: <2s
    p95: <5s
    p99: <10s
  throughput:
    requests_per_minute: >10
  resource_usage:
    memory: <512MB
    cpu: <50%
```

### Step 5: Edge Case Testing

Test boundary conditions:

```yaml
edge_cases:
  - empty_input
  - malformed_input
  - extremely_large_input
  - conflicting_requirements
  - missing_dependencies
  - concurrent_requests
  - timeout_scenarios
  - resource_exhaustion
```

### Step 6: Security Testing

Validate security aspects:

```yaml
security_tests:
  - input_sanitization
  - sql_injection_prevention
  - xss_prevention
  - secret_handling
  - access_control
  - audit_logging
```

### Step 7: Generate Test Report

Create comprehensive test report:

```markdown
# Test Report: {agent-name}

## Executive Summary

- **Total Tests**: {total}
- **Passed**: {passed} ({percentage}%)
- **Failed**: {failed}
- **Skipped**: {skipped}
- **Duration**: {duration}

## Test Results by Capability

### design-schema
✓ Multi-tenant schema design (1.2s)
✓ Complex relationships (2.1s)
✓ Migration generation (0.8s)
✗ Edge case: Circular dependencies (timeout)

### optimize-queries
✓ Index recommendation (0.5s)
✓ Query rewriting (1.1s)
✓ Performance estimation (0.3s)

## Performance Benchmarks

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| p50 response time | <2s | 1.4s | ✓ |
| p95 response time | <5s | 3.8s | ✓ |
| p99 response time | <10s | 12.3s | ✗ |

## Failed Tests

### Test: Circular dependency detection
**Status**: Failed (timeout after 30s)
**Issue**: Agent doesn't detect circular foreign key references
**Fix Required**: Add dependency cycle detection

## Edge Cases

| Scenario | Status | Notes |
|----------|--------|-------|
| Empty input | ✓ Pass | Proper error message |
| Large schema (100+ tables) | ✗ Fail | Exceeds memory limit |
| Invalid SQL | ✓ Pass | Caught and reported |

## Recommendations

1. **Critical**: Fix circular dependency detection
2. **High**: Optimize for large schemas (>50 tables)
3. **Medium**: Improve p99 latency
4. **Low**: Add more examples to documentation

## Next Steps

- Fix failed tests
- Re-run comprehensive suite
- Proceed to /agent-foundry/train if >95% pass rate
```

## Usage Examples

### Example 1: Smoke Test

```bash
/agent-foundry/test database-architect --suite smoke
```

Output:

```
Running smoke tests for database-architect...
✓ 5/5 tests passed (12s)

Ready for integration testing
```

### Example 2: Full Test with Coverage

```bash
/agent-foundry/test security-auditor --suite comprehensive --coverage
```

Output:

```
Running comprehensive tests for security-auditor...
✓ 47/50 tests passed (18m)
✗ 3 edge case failures

Coverage: 94.2%
Recommendation: Fix edge cases before training
```

### Example 3: Integration Tests

```bash
/agent-foundry/test cost-optimizer --suite integration
```

Tests multi-step workflows and agent collaboration.

## Test Categories

### Category 1: Functional Tests

Does the agent do what it's supposed to?

### Category 2: Non-Functional Tests

Performance, security, scalability

### Category 3: Integration Tests

Works with other agents and systems

### Category 4: Regression Tests

Previously fixed issues don't reoccur

### Category 5: User Acceptance Tests

Meets user expectations and needs

## Quality Gates

Before proceeding to training:

✅ ≥95% test pass rate
✅ All critical capabilities working
✅ Performance within targets
✅ No security vulnerabilities
✅ Edge cases handled gracefully
✅ Documentation matches behavior
✅ Integration tests pass

## Continuous Testing

Set up automated testing:

```yaml
# .github/workflows/agent-tests.yml
name: Agent Tests

on:
  push:
    paths:
      - '.claude/agents/**'
      - '.claude/commands/**'

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run smoke tests
        run: /agent-foundry/test $AGENT_NAME --suite smoke
      - name: Run integration tests
        run: /agent-foundry/test $AGENT_NAME --suite integration
```

## Troubleshooting

### Issue: Tests timing out

**Solution**: Increase timeout threshold, optimize agent logic

### Issue: Flaky tests

**Solution**: Add proper wait conditions, fix race conditions

### Issue: Low coverage

**Solution**: Add more test scenarios, test edge cases

### Issue: Performance degradation

**Solution**: Profile agent, optimize slow operations
