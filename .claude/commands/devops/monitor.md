---
description: Set up comprehensive infrastructure monitoring with dashboards and alerts
argument-hint: [--environment <prod|staging|dev>] [--platform <grafana|datadog|cloudwatch>]
allowed-tools: Task, Bash, Write, AskUserQuestion
model: claude-sonnet-4-5
timeout: 900
retry: 2
cost_estimate: 0.15-0.25

validation:
  input:
    environment:
      required: false
      default: "production"
      allowed_values: ["production", "staging", "development", "all"]
  output:
    schema: .claude/validation/schemas/devops/monitor-output.json
    required_files:
      - 'monitoring/monitoring-config.{yaml,json}'
    min_file_size: 300
    quality_threshold: 0.85
    content_requirements:
      - "Monitoring enabled for infrastructure"
      - "Dashboards created (≥1)"
      - "Alert rules configured"
      - "Notification channels setup"

version: 2.0.0
changelog:
  - version: 2.0.0
    date: 2026-01-20
    changes:
      - "Migrated to modern pattern with comprehensive validation"
      - "Added output validation for monitoring setup"
      - "Streamlined from 311 lines to focused workflow"
      - "Multi-platform support (Grafana/Datadog/CloudWatch)"
  - version: 1.0.0
    date: 2025-09-05
    changes:
      - "Initial implementation with Grafana support"
---

# Setup Infrastructure Monitoring

Environment: **${ARGUMENTS:-production}**

## Step 1: Validate Input & Parse Arguments

```bash
ARGS="$ARGUMENTS"
ENVIRONMENT=$(echo "$ARGS" | grep -oP '\-\-environment\s+\K\w+' || echo "production")
PLATFORM=$(echo "$ARGS" | grep -oP '\-\-platform\s+\K\w+' || echo "grafana")

echo "Environment: $ENVIRONMENT"
echo "Platform: $PLATFORM"
echo "✓ Input validated"
```

## Step 2: Setup Monitoring Using Agent

```javascript
const ENVIRONMENT = process.env.ENVIRONMENT || 'production';
const PLATFORM = process.env.PLATFORM || 'grafana';

await Task({
  subagent_type: 'general-purpose',
  description: 'Setup infrastructure monitoring',
  prompt: `Set up comprehensive infrastructure monitoring for ${ENVIRONMENT} environment using ${PLATFORM}.

MONITORING REQUIREMENTS:

**1. Metrics Collection**:
Configure collection of:
- CPU usage (per instance, aggregate)
- Memory usage (used, available, swap)
- Disk I/O (read/write ops, throughput)
- Network traffic (in/out bandwidth, connections)
- Application metrics (request rate, latency, errors)
- Database metrics (connections, queries, slow queries)

**2. Dashboard Creation**:
Create dashboards for:
- Infrastructure overview (CPU, memory, disk, network)
- Application performance (requests, latency, errors)
- Database health (connections, query performance)
- Alerts summary (active alerts, alert history)

**3. Alert Rules**:
Configure alerts for:
- Critical: CPU > 90% for 5min, Memory > 95%, Disk > 90%
- High: Error rate > 5%, Latency p99 > 2s, Database connections > 80%
- Medium: CPU > 70% for 15min, Memory > 80%
- Low: Disk > 70%, API rate limit approaching

**4. Notification Channels**:
Setup notifications via:
- Slack (critical/high alerts)
- Email (all alert levels)
- PagerDuty (production critical only)

**5. Platform-Specific Setup**:

${PLATFORM === 'grafana' ? `
**Grafana Setup**:
- Install Grafana server (if not exists)
- Configure Prometheus datasource
- Import pre-built dashboards
- Create custom dashboards
- Configure alert notification channels
- Setup alert rules in Prometheus
` : ''}

${PLATFORM === 'datadog' ? `
**Datadog Setup**:
- Install Datadog agent on all instances
- Configure API key
- Enable infrastructure monitoring
- Create custom dashboards
- Configure alert monitors
- Setup notification integrations
` : ''}

${PLATFORM === 'cloudwatch' ? `
**CloudWatch Setup**:
- Enable CloudWatch metrics
- Create CloudWatch dashboards
- Configure CloudWatch alarms
- Setup SNS topics for notifications
- Create log groups for application logs
` : ''}

**6. Generate Monitoring Config**:
Save configuration to: monitoring/monitoring-config.yaml
Include:
- Metrics collection config
- Dashboard definitions (or URLs)
- Alert rule definitions
- Notification channel config
- Platform-specific settings

**7. Verification**:
- Test metrics are being collected
- Verify dashboards are accessible
- Test alert rules (simulate conditions)
- Verify notifications working

Provide:
- Dashboard URLs
- Alert count configured
- Notification channels setup`,

  context: {
    environment: ENVIRONMENT,
    platform: PLATFORM,
    config_output: 'monitoring/monitoring-config.yaml'
  }
});
```

## Step 3: Validate Output

```bash
MONITORING_CONFIG="monitoring/monitoring-config.yaml"

# Check monitoring config created
if [ ! -f "$MONITORING_CONFIG" ]; then
  echo "❌ ERROR: Monitoring config not created"
  exit 1
fi

# Check minimum file size
FILE_SIZE=$(wc -c < "$MONITORING_CONFIG")
if [ $FILE_SIZE -lt 300 ]; then
  echo "❌ ERROR: Monitoring config too small (< 300 bytes)"
  echo "Size: $FILE_SIZE bytes"
  exit 1
fi

echo "✓ Output validation complete"
echo "  Config: $MONITORING_CONFIG"
echo "  Size: $FILE_SIZE bytes"
```

## Completion

```
═══════════════════════════════════════════════════
    INFRASTRUCTURE MONITORING SETUP COMPLETE ✓
═══════════════════════════════════════════════════

Environment: $ENVIRONMENT
Platform: $PLATFORM
Command: /devops/monitor
Version: 2.0.0

Monitoring Configured:
  ✓ Metrics collection enabled
  ✓ Dashboards created
  ✓ Alert rules configured
  ✓ Notifications setup

Dashboards:
  → [dashboard-urls]

Alerts Configured: [count]
Notification Channels: [count]

Validations Passed:
  ✓ Input validation
  ✓ Output validation (config created)
  ✓ Quality threshold (≥0.85)

NEXT STEPS:
→ Access dashboards at provided URLs
→ Test alert notifications
→ Monitor infrastructure health
→ Adjust thresholds as needed

═══════════════════════════════════════════════════
```

## Guidelines

- **Monitor Everything**: CPU, memory, disk, network, application, database
- **Alert Smartly**: Balance between too many and too few alerts
- **Dashboard Design**: Group related metrics, use meaningful visualizations
- **Test Alerts**: Simulate alert conditions to verify notifications work
- **Regular Review**: Review and adjust alert thresholds based on patterns
- **Document Runbooks**: Link alerts to runbooks for incident response
