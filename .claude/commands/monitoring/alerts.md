---
description: Set up alert policies and notification channels
argument-hint: [--service service-name] [--severity critical|high|medium|low] [--channel slack|email|pagerduty|webhook]
model: claude-sonnet-4-5-20250929
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---

Set up monitoring alerts: **${ARGUMENTS:-critical alerts for all services}**

## What This Command Does

Configures intelligent alerting policies with:

- **Threshold-based alerts** - Trigger when metrics exceed defined thresholds
- **Anomaly detection** - AI-powered detection of unusual patterns
- **Multi-channel notifications** - Slack, email, PagerDuty, webhooks, SMS
- **Alert routing** - Route to correct team based on severity and service
- **Escalation policies** - Automatic escalation if alerts aren't acknowledged
- **Alert suppression** - Prevent alert fatigue with smart deduplication

This command creates production-ready alert configurations that balance sensitivity with noise reduction, ensuring teams are notified of real issues without false alarm fatigue.

## Usage Examples

### Set Up Critical Alerts for Production Service

```bash
# Default critical alerts (error rate, availability, latency)
/monitoring:alerts --service api-gateway --severity critical

# All severity levels
/monitoring:alerts --service user-service

# Route to specific channel
/monitoring:alerts --service payment-processor --channel pagerduty
```

### Multi-Channel Alert Configuration

```bash
# Critical to PagerDuty, warnings to Slack
/monitoring:alerts --severity critical --channel pagerduty
/monitoring:alerts --severity high --channel slack

# Email for informational alerts
/monitoring:alerts --severity low --channel email
```

### Service-Specific Alerts

```bash
# Database-specific alerts
/monitoring:alerts --service postgres --severity high

# Queue-specific alerts
/monitoring:alerts --service rabbitmq --severity critical

# API endpoint-specific alerts
/monitoring:alerts --service api-gateway --severity critical
```

## Alert Categories

### Application Health Alerts (Critical)

**High Error Rate**

- **Threshold**: Error rate > 5% for 5 minutes
- **Impact**: Users experiencing failures
- **Channel**: PagerDuty (immediate response)
- **Runbook**: `/monitoring:runbook --issue high-error-rate`

**Service Unavailable**

- **Threshold**: Availability < 99% over 5 minutes
- **Impact**: Service down or degraded
- **Channel**: PagerDuty (immediate response)
- **Runbook**: `/monitoring:runbook --issue service-down`

**Extreme Latency**

- **Threshold**: P99 latency > 5 seconds for 5 minutes
- **Impact**: Severe performance degradation
- **Channel**: PagerDuty (immediate response)
- **Runbook**: `/monitoring:runbook --issue high-latency`

### Infrastructure Alerts (High Priority)

**High CPU Usage**

- **Threshold**: CPU > 85% for 10 minutes
- **Impact**: Performance degradation, potential crashes
- **Channel**: Slack + Email
- **Action**: Review auto-scaling, consider scaling up

**High Memory Usage**

- **Threshold**: Memory > 90% for 10 minutes
- **Impact**: Risk of OOM kills, crashes
- **Channel**: Slack + Email
- **Action**: Check for memory leaks, scale if needed

**Disk Space Critical**

- **Threshold**: Disk > 85% full
- **Impact**: Service crashes, data loss
- **Channel**: PagerDuty
- **Action**: Clean up logs, expand storage

**Database Connection Pool Exhausted**

- **Threshold**: Available connections < 10%
- **Impact**: New requests failing
- **Channel**: Slack + Email
- **Action**: Check for connection leaks, scale pool

### Performance Alerts (Medium Priority)

**Elevated Latency**

- **Threshold**: P95 latency > 2 seconds for 10 minutes
- **Impact**: User experience degradation
- **Channel**: Slack
- **Action**: Investigate slow queries, optimize

**Increased Cache Misses**

- **Threshold**: Cache hit rate < 80% for 15 minutes
- **Impact**: Increased database load, slower responses
- **Channel**: Slack
- **Action**: Review cache strategy, warm cache

**Queue Depth Growing**

- **Threshold**: Queue depth > 1000 messages for 15 minutes
- **Impact**: Processing delays
- **Channel**: Slack
- **Action**: Scale workers, investigate bottlenecks

### Business Impact Alerts (Variable Priority)

**Failed Transactions**

- **Threshold**: Transaction failure rate > 2%
- **Impact**: Revenue loss, customer dissatisfaction
- **Channel**: PagerDuty + Slack
- **Priority**: Critical

**Payment Processing Errors**

- **Threshold**: Any payment error
- **Impact**: Direct revenue loss
- **Channel**: PagerDuty (immediate)
- **Priority**: Critical

**User Sign-up Failures**

- **Threshold**: Sign-up failure > 10%
- **Impact**: Growth impact
- **Channel**: Slack + Email
- **Priority**: High

## Prometheus Alert Rules Configuration

```yaml
groups:
  - name: application_health
    interval: 30s
    rules:
      # High error rate alert
      - alert: HighErrorRate
        expr: |
          (
            rate(http_requests_total{status=~"5.."}[5m])
            /
            rate(http_requests_total[5m])
          ) * 100 > 5
        for: 5m
        labels:
          severity: critical
          team: platform
        annotations:
          summary: "High error rate detected on {{ $labels.service }}"
          description: "Error rate is {{ $value | humanizePercentage }} (threshold: 5%)"
          runbook: "https://wiki.company.com/runbooks/high-error-rate"
          dashboard: "https://grafana.company.com/d/service-health"

      # Service down alert
      - alert: ServiceDown
        expr: up{job="service"} == 0
        for: 1m
        labels:
          severity: critical
          team: platform
        annotations:
          summary: "Service {{ $labels.service }} is down"
          description: "Service has been unreachable for 1 minute"
          runbook: "https://wiki.company.com/runbooks/service-down"

      # High latency alert
      - alert: HighLatency
        expr: |
          histogram_quantile(0.99,
            rate(http_request_duration_seconds_bucket[5m])
          ) > 5
        for: 5m
        labels:
          severity: critical
          team: platform
        annotations:
          summary: "High latency on {{ $labels.service }}"
          description: "P99 latency is {{ $value | humanizeDuration }} (threshold: 5s)"
          runbook: "https://wiki.company.com/runbooks/high-latency"

  - name: infrastructure
    interval: 60s
    rules:
      # High CPU usage
      - alert: HighCPUUsage
        expr: |
          (
            rate(process_cpu_seconds_total[5m]) * 100
          ) > 85
        for: 10m
        labels:
          severity: warning
          team: infrastructure
        annotations:
          summary: "High CPU usage on {{ $labels.instance }}"
          description: "CPU usage is {{ $value | humanize }}% (threshold: 85%)"
          action: "Consider scaling or investigating CPU-intensive processes"

      # High memory usage
      - alert: HighMemoryUsage
        expr: |
          (
            process_resident_memory_bytes / node_memory_MemTotal_bytes
          ) * 100 > 90
        for: 10m
        labels:
          severity: warning
          team: infrastructure
        annotations:
          summary: "High memory usage on {{ $labels.instance }}"
          description: "Memory usage is {{ $value | humanize }}% (threshold: 90%)"
          action: "Check for memory leaks or scale up memory"

      # Disk space critical
      - alert: DiskSpaceCritical
        expr: |
          (
            node_filesystem_avail_bytes / node_filesystem_size_bytes
          ) * 100 < 15
        for: 5m
        labels:
          severity: critical
          team: infrastructure
        annotations:
          summary: "Disk space critical on {{ $labels.instance }}"
          description: "Only {{ $value | humanize }}% disk space remaining"
          action: "Clean up logs or expand storage immediately"

      # Database connection pool exhausted
      - alert: DatabaseConnectionPoolExhausted
        expr: |
          (
            pg_stat_activity_count / pg_settings_max_connections
          ) * 100 > 90
        for: 5m
        labels:
          severity: critical
          team: database
        annotations:
          summary: "Database connection pool nearly exhausted"
          description: "{{ $value | humanize }}% of connections in use"
          action: "Check for connection leaks, increase pool size"

  - name: business_metrics
    interval: 60s
    rules:
      # Failed transactions
      - alert: HighTransactionFailureRate
        expr: |
          (
            rate(transactions_total{status="failed"}[5m])
            /
            rate(transactions_total[5m])
          ) * 100 > 2
        for: 5m
        labels:
          severity: critical
          team: business
        annotations:
          summary: "High transaction failure rate"
          description: "Transaction failure rate is {{ $value | humanizePercentage }}"
          impact: "Revenue loss, customer dissatisfaction"
          runbook: "https://wiki.company.com/runbooks/transaction-failures"

      # Payment processing errors
      - alert: PaymentProcessingError
        expr: rate(payment_errors_total[1m]) > 0
        for: 1m
        labels:
          severity: critical
          team: payments
        annotations:
          summary: "Payment processing errors detected"
          description: "{{ $value }} payment errors in the last minute"
          impact: "Direct revenue loss"
          escalate: "Escalate to payment processor if persistent"
```

## Grafana Alert Configuration

```json
{
  "alert": {
    "name": "High Error Rate",
    "message": "Error rate is above 5% on {{service}}",
    "conditions": [
      {
        "evaluator": {
          "params": [5],
          "type": "gt"
        },
        "operator": {
          "type": "and"
        },
        "query": {
          "params": ["A", "5m", "now"]
        },
        "reducer": {
          "params": [],
          "type": "avg"
        },
        "type": "query"
      }
    ],
    "executionErrorState": "alerting",
    "for": "5m",
    "frequency": "60s",
    "handler": 1,
    "noDataState": "no_data",
    "notifications": [
      {
        "uid": "slack-critical"
      },
      {
        "uid": "pagerduty-oncall"
      }
    ]
  }
}
```

## Datadog Alert Configuration

```json
{
  "name": "High Error Rate - Production API",
  "type": "metric alert",
  "query": "avg(last_5m):sum:trace.http.request.errors{env:production,service:api}.as_rate() > 0.05",
  "message": "Error rate is above 5% on production API.\n\n@slack-platform-alerts @pagerduty-oncall\n\n{{#is_alert}}\nDashboard: https://app.datadoghq.com/dashboard/api-health\nRunbook: https://wiki.company.com/runbooks/high-error-rate\n{{/is_alert}}",
  "tags": ["env:production", "service:api", "team:platform"],
  "options": {
    "thresholds": {
      "critical": 0.05,
      "warning": 0.02
    },
    "notify_no_data": true,
    "no_data_timeframe": 10,
    "notify_audit": false,
    "require_full_window": false,
    "new_host_delay": 300,
    "include_tags": true,
    "escalation_message": "Error rate still elevated after 15 minutes. @oncall-lead",
    "renotify_interval": 60
  },
  "priority": 1,
  "restricted_roles": null
}
```

## CloudWatch Alarm Configuration

```json
{
  "AlarmName": "HighErrorRate-ProductionAPI",
  "AlarmDescription": "Triggers when API error rate exceeds 5%",
  "ActionsEnabled": true,
  "AlarmActions": [
    "arn:aws:sns:us-east-1:123456789012:critical-alerts"
  ],
  "MetricName": "4XXError",
  "Namespace": "AWS/ApiGateway",
  "Statistic": "Average",
  "Dimensions": [
    {
      "Name": "ApiName",
      "Value": "ProductionAPI"
    }
  ],
  "Period": 300,
  "EvaluationPeriods": 1,
  "Threshold": 5.0,
  "ComparisonOperator": "GreaterThanThreshold",
  "TreatMissingData": "notBreaching"
}
```

## Notification Channel Configuration

### Slack Integration

```yaml
# Alertmanager configuration
receivers:
  - name: 'slack-critical'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
        channel: '#alerts-critical'
        title: '{{ .GroupLabels.alertname }}'
        text: >-
          {{ range .Alerts }}
          *Alert:* {{ .Annotations.summary }}
          *Description:* {{ .Annotations.description }}
          *Severity:* {{ .Labels.severity }}
          *Runbook:* {{ .Annotations.runbook }}
          {{ end }}
        send_resolved: true

  - name: 'slack-warnings'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
        channel: '#alerts-warnings'
        title: '{{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
        send_resolved: true
```

### PagerDuty Integration

```yaml
receivers:
  - name: 'pagerduty-oncall'
    pagerduty_configs:
      - service_key: 'YOUR_PAGERDUTY_SERVICE_KEY'
        description: '{{ .GroupLabels.alertname }}: {{ .CommonAnnotations.summary }}'
        details:
          firing: '{{ .Alerts.Firing | len }}'
          resolved: '{{ .Alerts.Resolved | len }}'
          severity: '{{ .CommonLabels.severity }}'
          runbook: '{{ .CommonAnnotations.runbook }}'
```

### Email Integration

```yaml
receivers:
  - name: 'email-team'
    email_configs:
      - to: 'platform-team@company.com'
        from: 'alerts@company.com'
        smarthost: 'smtp.company.com:587'
        auth_username: 'alerts@company.com'
        auth_password: 'PASSWORD'
        headers:
          Subject: '[{{ .Status | toUpper }}] {{ .GroupLabels.alertname }}'
        html: |
          <h3>{{ .GroupLabels.alertname }}</h3>
          {{ range .Alerts }}
          <p><b>Summary:</b> {{ .Annotations.summary }}</p>
          <p><b>Description:</b> {{ .Annotations.description }}</p>
          <p><b>Severity:</b> {{ .Labels.severity }}</p>
          <p><b>Runbook:</b> <a href="{{ .Annotations.runbook }}">View</a></p>
          {{ end }}
```

### Webhook Integration

```yaml
receivers:
  - name: 'webhook-custom'
    webhook_configs:
      - url: 'https://api.company.com/alerts/webhook'
        send_resolved: true
        http_config:
          basic_auth:
            username: 'webhook_user'
            password: 'webhook_password'
```

## Alert Routing Strategy

```yaml
# Alertmanager routing configuration
route:
  receiver: 'default'
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 10s
  group_interval: 5m
  repeat_interval: 4h

  routes:
    # Critical alerts go to PagerDuty
    - match:
        severity: critical
      receiver: 'pagerduty-oncall'
      continue: true
      repeat_interval: 15m

    # Critical alerts also go to Slack
    - match:
        severity: critical
      receiver: 'slack-critical'

    # High priority to Slack + Email
    - match:
        severity: high
      receiver: 'slack-warnings'
      continue: true

    - match:
        severity: high
      receiver: 'email-team'

    # Medium priority to Slack only
    - match:
        severity: medium
      receiver: 'slack-warnings'

    # Low priority to email only
    - match:
        severity: low
      receiver: 'email-team'
      group_interval: 24h
      repeat_interval: 24h
```

## Alert Best Practices

### Threshold Tuning

- Start conservative (higher thresholds) and tighten based on data
- Use percentiles (p95, p99) for latency, not averages
- Set appropriate "for" durations to avoid flapping (5-10 minutes typical)
- Review and adjust thresholds quarterly based on traffic patterns

### Alert Fatigue Prevention

- Limit alerts to actionable items only
- Use severity levels appropriately (not everything is critical)
- Group related alerts to avoid notification storms
- Set repeat intervals to prevent spam (15m for critical, 4h for warnings)
- Implement alert suppression during maintenance windows

### Context in Alerts

- Include dashboard links in alert messages
- Link to relevant runbooks
- Show current value vs threshold
- Add business impact description
- Include suggested actions or next steps

### Escalation Policies

- Tier 1: On-call engineer (PagerDuty)
- Tier 2: Team lead (if not acknowledged in 15 minutes)
- Tier 3: Engineering manager (if not acknowledged in 30 minutes)
- Auto-create incident tickets for critical alerts

## Business Value & ROI

### Faster Incident Response

- **MTTD (Mean Time To Detect)**: Reduced from 15 minutes to < 1 minute
- **MTTR (Mean Time To Resolve)**: Reduced by 40-60%
- **Impact**: $10,000-$100,000 saved per major incident
- **Customer Impact**: Minimize user-facing downtime

### Prevent Outages

- **Proactive Alerts**: Catch issues before customers affected
- **Example**: High memory usage alert → scale up → prevent crash
- **Impact**: Prevent 50-80% of potential outages
- **Value**: Each prevented outage saves $50,000-$500,000

### Operational Efficiency

- **Automated Triage**: Alerts include context and runbooks
- **Reduced Toil**: No manual monitoring required
- **On-call Relief**: Clear escalation reduces burnout
- **Value**: Save 10-20 hours per week of manual monitoring

### Data-Driven Optimization

- **Alert Analytics**: Track which alerts fire most frequently
- **Threshold Tuning**: Continuously improve signal-to-noise ratio
- **Performance Trends**: Identify degradation before it becomes critical
- **Value**: Continuous improvement of system reliability

## Success Metrics

Track these KPIs to measure alerting effectiveness:

1. **Alert Accuracy**: > 90% of alerts are actionable
2. **False Positive Rate**: < 10% of alerts
3. **MTTD**: < 1 minute for critical issues
4. **MTTR**: 50% reduction from baseline
5. **Alert Acknowledgment Time**: < 5 minutes for critical
6. **Escalation Rate**: < 20% of alerts escalate to Tier 2
7. **Notification Delivery**: 99.9% success rate
8. **Team Satisfaction**: Regular surveys show alerts are helpful

## Integration with Other Commands

### Workflow Integration

- `/monitoring:dashboard` - Create dashboards for alert visualization
- `/monitoring:alerts` - Configure alert policies (this command)
- `/monitoring:slo` - Define SLOs that drive alert thresholds
- `/monitoring:runbook` - Create runbooks linked from alerts

### Incident Response

1. Alert fires → Notification sent to on-call
2. Engineer views dashboard (link in alert)
3. Follows runbook (link in alert)
4. Uses `/devops:debug` to investigate
5. Uses `/devops:rollback` if needed
6. Alert resolves automatically when metrics normalize

### Continuous Improvement

- Review alert history weekly
- Tune thresholds based on false positives
- Update runbooks based on incident learnings
- Add new alerts for newly discovered failure modes

## Example Implementation

```bash
# Create Prometheus alert rules
cat > alerts.yml <<'EOF'
groups:
  - name: application_health
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate on {{ $labels.service }}"
EOF

# Reload Prometheus configuration
curl -X POST http://localhost:9090/-/reload

# Configure Alertmanager
cat > alertmanager.yml <<'EOF'
route:
  receiver: 'default'
  routes:
    - match:
        severity: critical
      receiver: 'pagerduty-oncall'

receivers:
  - name: 'pagerduty-oncall'
    pagerduty_configs:
      - service_key: 'YOUR_KEY'
EOF

# Test alert
curl -X POST http://localhost:9093/api/v1/alerts \
  -H 'Content-Type: application/json' \
  -d '[{
    "labels": {"alertname": "TestAlert", "severity": "critical"},
    "annotations": {"summary": "This is a test alert"}
  }]'
```

## Success Criteria

- Alert rules configured for all critical services
- Multi-channel notifications working (Slack, email, PagerDuty)
- Alert routing directs alerts to correct teams
- Escalation policies defined and tested
- False positive rate < 10%
- All alerts include dashboard links and runbooks
- Alert configuration version controlled
- Team trained on alert response procedures
- On-call rotation established
- Post-incident reviews include alert effectiveness

---
**Related Commands**: `/monitoring:dashboard`, `/monitoring:slo`, `/monitoring:runbook`, `/devops:debug`, `/devops:rollback`
