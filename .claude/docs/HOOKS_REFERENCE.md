# Claude Code Hooks Reference

**Version**: 1.0.0
**Last Updated**: 2026-01-20
**Status**: Production Ready

## Table of Contents

1. [Overview](#overview)
2. [Hook System Architecture](#hook-system-architecture)
3. [Hook Types](#hook-types)
4. [Production Hooks](#production-hooks)
5. [Hook Configuration](#hook-configuration)
6. [Creating Custom Hooks](#creating-custom-hooks)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)
9. [Metrics & Monitoring](#metrics--monitoring)

---

## Overview

The hook system provides **event-driven automation** for the Mahoosuc Operating System, enabling automated quality gates, deployment safety, intelligent file monitoring, and proactive system maintenance.

### Benefits

- **Automation**: Eliminate manual quality checks and repetitive tasks
- **Safety**: Prevent bad code from reaching production
- **Efficiency**: Reduce deployment cycles from hours to minutes
- **Proactivity**: Catch issues before they become problems
- **Consistency**: Enforce standards automatically

### Key Features

- ✅ **Event-Driven**: Respond to commits, deploys, file changes, errors, and time-based schedules
- ✅ **Validation**: Block bad commits, failed tests, and unsafe deployments
- ✅ **Auto-Recovery**: Automatically handle known errors and issues
- ✅ **Intelligent Routing**: Context-aware notifications and escalations
- ✅ **Metrics Tracking**: Monitor hook performance and system health

---

## Hook System Architecture

### Directory Structure

```text
.claude/hooks/
├── pre-commit/           # Hooks that run before git commits
│   └── quality-gate.yaml
├── post-deploy/          # Hooks that run after deployments
│   └── verification.yaml
├── on-file-change/       # Hooks that watch for file changes
│   └── auto-spec-tasks.yaml
├── on-error/             # Hooks that respond to errors
│   └── notification.yaml
├── periodic/             # Scheduled hooks (cron-like)
│   └── health-check.yaml
├── logs/                 # Hook execution logs
├── data/                 # Hook persistent data
└── reports/              # Generated reports
```

### Hook Lifecycle

```text
Event Trigger → Hook Detection → Validation → Execution → Reporting → Metrics
```

1. **Event Trigger**: Something happens (commit, deploy, file change, error, schedule)
2. **Hook Detection**: System finds matching hooks for the event
3. **Validation**: Hook validates pre-conditions and configuration
4. **Execution**: Hook steps run sequentially or in parallel
5. **Reporting**: Results logged, notifications sent, incidents created
6. **Metrics**: Performance data collected and analyzed

---

## Hook Types

### 1. Pre-Commit Hooks (`pre-commit/`)

**Trigger**: Before git commit
**Purpose**: Quality gates and validation
**Behavior**: Can block commits if checks fail

**Use Cases**:

- Run test suites
- Check code quality and linting
- Verify accessibility compliance
- Security vulnerability scanning
- Type checking

**Example**: `.claude/hooks/pre-commit/quality-gate.yaml`

### 2. Post-Deploy Hooks (`post-deploy/`)

**Trigger**: After deployment completes
**Purpose**: Deployment verification and monitoring
**Behavior**: Can trigger rollbacks if verification fails

**Use Cases**:

- Health checks
- Smoke tests
- Performance monitoring
- Database migration verification
- Integration testing

**Example**: `.claude/hooks/post-deploy/verification.yaml`

### 3. File Change Hooks (`on-file-change/`)

**Trigger**: When files are created, modified, or deleted
**Purpose**: Automated workflows based on file changes
**Behavior**: Watches specific file patterns

**Use Cases**:

- Auto-generate tasks when specs are completed
- Update documentation when code changes
- Trigger builds when source files change
- Sync data between systems

**Example**: `.claude/hooks/on-file-change/auto-spec-tasks.yaml`

### 4. Error Hooks (`on-error/`)

**Trigger**: When commands or operations fail
**Purpose**: Intelligent error handling and notification
**Behavior**: Classifies errors and routes appropriately

**Use Cases**:

- Send alerts for critical failures
- Create incident tickets
- Suggest error fixes
- Attempt auto-recovery
- Escalate to on-call engineers

**Example**: `.claude/hooks/on-error/notification.yaml`

### 5. Periodic Hooks (`periodic/`)

**Trigger**: Time-based schedules (cron-like)
**Purpose**: Scheduled maintenance and monitoring
**Behavior**: Runs at configured intervals

**Use Cases**:

- Daily system health checks
- Weekly dependency audits
- Monthly security scans
- Automated cleanup tasks
- Performance trending

**Example**: `.claude/hooks/periodic/health-check.yaml`

---

## Production Hooks

### Pre-Commit Quality Gate

**File**: `.claude/hooks/pre-commit/quality-gate.yaml`

**Purpose**: Ensure code quality before commits

**Checks**:

1. ✅ Test Suite - All tests must pass
2. ✅ Accessibility - No critical WCAG violations
3. ⚠️ Security Audit - Warn on vulnerabilities
4. ⚠️ Code Quality - Linting and formatting
5. ✅ Type Check - TypeScript validation

**Configuration**:

```yaml
block_on_failure: true  # Block commit if critical checks fail
parallel_execution: true  # Run checks in parallel
timeout: 600  # 10 minutes max
```

**Skip Conditions**:

- Branches: `wip/*`, `draft/*`
- Commit messages: `^WIP:`, `^DRAFT:`, `^docs:`

**Expected Impact**:

- 80% reduction in bugs reaching production
- 30-40% reduction in code review time
- Zero accessibility regressions

---

### Post-Deploy Verification

**File**: `.claude/hooks/post-deploy/verification.yaml`

**Purpose**: Verify deployment success and trigger rollbacks if needed

**Checks**:

1. ✅ Health Check - All services healthy
2. ✅ Smoke Tests - Critical paths functional
3. ✅ Performance Monitoring - No degradation
4. ✅ Database Migrations - Successfully applied
5. ⚠️ Integration Tests - End-to-end validation

**Rollback Triggers**:

- Health check fails
- Smoke tests fail
- Database migration fails
- Response time > 500ms (p95)
- Error rate > 1%

**Expected Impact**:

- 90% reduction in failed deployments
- 50% faster rollback time
- 95% deployment success rate

---

### Auto Spec Tasks Creation

**File**: `.claude/hooks/on-file-change/auto-spec-tasks.yaml`

**Purpose**: Automatically create implementation tasks when spec is completed

**Trigger Patterns**:

- `agent-os/specs/*/spec.md`
- `agent-os/specs/*/requirements.md`

**Completion Markers**:

- `## Specification Complete`
- `Status: Ready for Implementation`
- `<!-- SPEC_COMPLETE -->`

**Actions**:

1. Validate spec completeness (80% threshold)
2. Create implementation tasks (`/agent-os/create-tasks`)
3. Notify team via email
4. Update product roadmap

**Expected Impact**:

- 100% consistency in task creation
- 4-8 hours saved per spec
- Zero forgotten specs

---

### Error Notification & Recovery

**File**: `.claude/hooks/on-error/notification.yaml`

**Purpose**: Intelligent error handling with automated recovery

**Error Classification**:

- **Critical**: deployment_failure, database_connection_lost, security_breach
- **High**: test_suite_failure, api_integration_failure, performance_degradation
- **Medium**: accessibility_violations, linting_errors, deprecated_api_usage
- **Low**: warning_messages, optimization_suggestions

**Notification Routing**:

- **Critical**: PagerDuty + Slack + Email + SMS
- **High**: Slack + Email
- **Medium**: Slack
- **Low**: Console only

**Auto-Recovery Strategies**:

- Retry with exponential backoff
- Clear cache and retry
- Restart service
- Rollback change

**Expected Impact**:

- 60% of errors auto-recovered
- Mean time to recovery: 5 minutes (vs 30 minutes manual)
- 30% reduction in escalations

---

### Periodic Health Check

**File**: `.claude/hooks/periodic/health-check.yaml`

**Purpose**: Daily comprehensive system health audit

**Schedule**: Daily at 3:00 AM (configurable)

**Health Categories**:

1. **Code**: Quality scan, linting, best practices
2. **Dependencies**: Vulnerability audit, outdated packages
3. **Infrastructure**: Service uptime, disk usage, memory
4. **Database**: Performance, integrity, optimization
5. **Security**: Vulnerability scan, compliance check
6. **Monitoring**: Alert health, monitoring uptime

**Maintenance Tasks**:

- Cleanup logs > 30 days old
- Remove temporary files > 7 days old
- Check for dependency updates
- Clear expired cache entries

**Reporting**:

- Markdown report: `.claude/hooks/reports/health-check-YYYY-MM-DD.md`
- JSON report: `.claude/hooks/reports/health-check-YYYY-MM-DD.json`
- Email summary (optional)
- Slack notification (optional)

**Expected Impact**:

- 50% reduction in unexpected outages
- 90-day health trend tracking
- Proactive issue detection

---

## Hook Configuration

### YAML Structure

```yaml
---
name: hook-name
version: 1.0.0
description: What this hook does
trigger: on-commit | on-deploy | on-file-change | on-error | periodic
priority: critical | high | medium | low
enabled: true

# Hook-specific configuration
config:
  timeout: 600
  parallel_execution: true
  retry: 3

# Execution steps
steps:
  - name: step-name
    description: Step description
    command: /command-to-run
    required: true
    timeout: 120
    on_failure:
      action: block | warn | log | retry | rollback
      message: "Failure message"
    validation:
      exit_code: 0
      required_output: "Expected output"

# Reporting
reporting:
  format: summary | detailed
  include_metrics: true
  log_file: path/to/log

# Metrics
metrics:
  track:
    - metric_name
  alert_thresholds:
    metric_name: value
---
```

### Configuration Fields

#### Top-Level Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | ✅ | Unique hook identifier |
| `version` | string | ✅ | Semantic version (1.0.0) |
| `description` | string | ✅ | What the hook does |
| `trigger` | enum | ✅ | Event type that triggers hook |
| `priority` | enum | ✅ | Execution priority level |
| `enabled` | boolean | ✅ | Whether hook is active |

#### Config Section

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `timeout` | number | 300 | Max execution time (seconds) |
| `parallel_execution` | boolean | false | Run steps in parallel |
| `retry` | number | 0 | Retry attempts on failure |

#### Step Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | ✅ | Step identifier |
| `description` | string | ✅ | What step does |
| `command` | string | ✅ | Command to execute |
| `required` | boolean | ❌ | Block if step fails |
| `timeout` | number | ❌ | Step timeout |
| `on_failure` | object | ❌ | Failure handling |
| `validation` | object | ❌ | Success criteria |

---

## Creating Custom Hooks

### Step 1: Choose Hook Type

Determine which event should trigger your hook:

- **Pre-Commit**: Quality gates, validation before commit
- **Post-Deploy**: Verification, monitoring after deployment
- **File Change**: Automation triggered by file modifications
- **Error**: Response to command/operation failures
- **Periodic**: Scheduled maintenance or monitoring

### Step 2: Create Hook File

Create a YAML file in the appropriate directory:

```bash
# Pre-commit hook
.claude/hooks/pre-commit/my-hook.yaml

# Post-deploy hook
.claude/hooks/post-deploy/my-hook.yaml

# File change hook
.claude/hooks/on-file-change/my-hook.yaml

# Error hook
.claude/hooks/on-error/my-hook.yaml

# Periodic hook
.claude/hooks/periodic/my-hook.yaml
```

### Step 3: Define Hook Configuration

```yaml
---
name: my-custom-hook
version: 1.0.0
description: Brief description of what this hook does
trigger: on-commit  # or on-deploy, on-file-change, on-error, periodic
priority: medium
enabled: true

config:
  timeout: 300
  parallel_execution: false
  retry: 1

steps:
  - name: my-check
    description: Perform some validation
    command: /my/command --arg value
    required: true
    timeout: 60
    on_failure:
      action: block
      message: "Check failed. Please fix before proceeding."
    validation:
      exit_code: 0

reporting:
  format: summary
  include_metrics: true
  log_file: .claude/hooks/logs/my-hook.log

metrics:
  track:
    - execution_time
    - success_rate
  alert_thresholds:
    success_rate: 0.9
---
```

### Step 4: Test Hook

Test your hook in isolation:

```bash
# Manually trigger hook (when hook system supports it)
claude-code hooks run my-custom-hook

# Check logs
cat .claude/hooks/logs/my-hook.log
```

### Step 5: Enable in Production

Once tested, enable the hook:

```yaml
enabled: true
```

---

## Best Practices

### Hook Design

1. **Single Responsibility**: Each hook should have one clear purpose
2. **Idempotent**: Hooks should be safe to run multiple times
3. **Fast by Default**: Optimize for speed; use timeouts aggressively
4. **Fail Fast**: Detect and report failures immediately
5. **Graceful Degradation**: Continue if non-critical steps fail

### Performance

1. **Parallel Execution**: Run independent steps in parallel
2. **Aggressive Timeouts**: Set realistic timeouts for each step
3. **Caching**: Cache expensive operations when possible
4. **Incremental Checks**: Only check changed files, not entire codebase
5. **Debouncing**: For file-change hooks, debounce to prevent spam

### Error Handling

1. **Clear Error Messages**: Make failures actionable
2. **Classify Severity**: Critical vs warn vs log
3. **Auto-Recovery**: Attempt recovery for known issues
4. **Escalation**: Route critical errors appropriately
5. **Context**: Capture system state and recent changes

### Notification

1. **Right Channel**: Match severity to notification urgency
2. **Deduplication**: Prevent duplicate alerts
3. **Batching**: Group low-priority notifications
4. **Actionable**: Include fix suggestions in alerts
5. **Quiet Hours**: Respect time zones and schedules

### Metrics

1. **Track Everything**: Execution time, success rate, failures
2. **Trend Analysis**: Compare against historical data
3. **Alert Thresholds**: Set realistic alert thresholds
4. **Dashboard**: Visualize hook performance
5. **Continuous Improvement**: Use metrics to optimize hooks

---

## Troubleshooting

### Hook Not Running

**Problem**: Hook doesn't execute when expected

**Solutions**:

1. Check `enabled: true` in hook configuration
2. Verify trigger condition matches event
3. Check conditional logic (skip_patterns, file_patterns)
4. Review hook logs: `.claude/hooks/logs/`
5. Verify hook file syntax (valid YAML)

### Hook Timing Out

**Problem**: Hook exceeds timeout and fails

**Solutions**:

1. Increase timeout values
2. Enable parallel execution
3. Optimize slow commands
4. Split into multiple smaller hooks
5. Cache expensive operations

### Hook Blocking Workflow

**Problem**: Hook blocks commits/deploys too aggressively

**Solutions**:

1. Change `action: block` to `action: warn`
2. Add skip patterns for specific scenarios
3. Adjust validation thresholds
4. Make non-critical steps `required: false`
5. Add override mechanism for emergencies

### Hook Failing Intermittently

**Problem**: Hook succeeds sometimes, fails others

**Solutions**:

1. Add retry logic (`retry: 3`)
2. Check for race conditions
3. Verify external dependencies (network, services)
4. Add health checks before execution
5. Review logs for patterns

### Too Many Notifications

**Problem**: Hook sends excessive alerts

**Solutions**:

1. Enable deduplication window
2. Increase severity thresholds
3. Batch low-priority notifications
4. Use `log_only` for informational messages
5. Adjust alert frequency

---

## Metrics & Monitoring

### Hook Performance Metrics

**Available Metrics**:

- `execution_time`: Time to complete hook
- `success_rate`: Percentage of successful executions
- `failure_count`: Number of failures
- `timeout_count`: Number of timeouts
- `retry_count`: Number of retries needed

**Alert Thresholds**:

```yaml
metrics:
  alert_thresholds:
    avg_execution_time: 300  # Warn if avg > 5 min
    success_rate: 0.9  # Warn if < 90%
    timeout_rate: 0.05  # Warn if > 5% timeout
```

### System Health Metrics

**Tracked Metrics**:

- Code quality score
- Dependency vulnerability count
- Infrastructure uptime
- Database performance
- Security compliance score

**Trend Analysis**:

- 30-day rolling averages
- Week-over-week comparisons
- Anomaly detection
- Degradation alerts

### Hook Logs

**Log Locations**:

- Individual hook logs: `.claude/hooks/logs/{hook-name}.log`
- Aggregated logs: `.claude/hooks/logs/all-hooks.log`
- Error logs: `.claude/hooks/logs/errors.log`

**Log Format**:

```text
[2026-01-20T18:54:23Z] [INFO] [pre-commit-quality-gate] Starting execution
[2026-01-20T18:54:25Z] [INFO] [pre-commit-quality-gate] Step: run-tests - STARTED
[2026-01-20T18:54:45Z] [SUCCESS] [pre-commit-quality-gate] Step: run-tests - PASSED (20s)
[2026-01-20T18:54:46Z] [INFO] [pre-commit-quality-gate] Step: accessibility-check - STARTED
[2026-01-20T18:54:50Z] [SUCCESS] [pre-commit-quality-gate] Step: accessibility-check - PASSED (4s)
[2026-01-20T18:54:52Z] [SUCCESS] [pre-commit-quality-gate] Execution complete (29s)
```

### Dashboards

**Recommended Dashboards**:

1. **Hook Performance**: Execution times, success rates, trends
2. **System Health**: Overall health score, category breakdowns
3. **Error Analysis**: Error frequency, types, recovery rates
4. **Deployment Safety**: Verification success, rollback frequency
5. **Cost Analysis**: Hook execution costs, optimization opportunities

---

## FAQ

### Can hooks call other hooks?

Yes, hooks can trigger other hooks or call slash commands that may trigger hooks. Be careful of infinite loops.

### Can I disable a hook temporarily?

Yes, set `enabled: false` in the hook configuration. The hook will be skipped until re-enabled.

### What happens if a hook crashes?

The hook system will log the error, send notifications (if configured), and continue with other hooks. Use `on_failure` to define specific behavior.

### Can hooks access secrets?

Yes, use environment variables for secrets: `${SLACK_WEBHOOK_URL}`, `${SENTRY_API_KEY}`, etc. Never hardcode secrets.

### How do I debug a failing hook?

1. Check logs in `.claude/hooks/logs/`
2. Run hook manually (if supported)
3. Enable verbose logging
4. Check validation criteria
5. Verify prerequisites

### Can I use hooks in CI/CD?

Yes, hooks are designed to work in CI/CD environments. They complement existing CI/CD workflows.

### What's the performance impact?

Minimal. Hooks run in parallel when possible and have aggressive timeouts. Pre-commit hooks average 30-60 seconds.

### Can I customize notification channels?

Yes, configure `reporting.notify.channels` to use Slack, Email, PagerDuty, SMS, or custom webhooks.

---

## Roadmap

### Planned Enhancements

- [ ] **Hook Marketplace**: Share and discover community hooks
- [ ] **Visual Hook Builder**: GUI for creating hooks
- [ ] **Hook Analytics**: Advanced metrics and insights
- [ ] **Hook Templates**: Pre-built hooks for common scenarios
- [ ] **Hook Testing Framework**: Unit test hooks before deployment
- [ ] **Hook Dependencies**: Define hook execution order
- [ ] **Conditional Hooks**: More advanced trigger logic
- [ ] **Hook Playground**: Test hooks in sandbox environment

---

## Support

### Getting Help

- **Documentation**: This file and `.claude/CLAUDE.md`
- **Examples**: See production hooks in `.claude/hooks/`
- **Issues**: Report problems via project issue tracker
- **Community**: Share hooks and best practices

### Contributing

To contribute a hook:

1. Create hook following best practices
2. Test thoroughly in development environment
3. Document hook purpose and configuration
4. Submit pull request with hook and documentation
5. Include metrics from testing

---

**Last Updated**: 2026-01-20
**Version**: 1.0.0
**Maintained By**: Mahoosuc Operating System Team
