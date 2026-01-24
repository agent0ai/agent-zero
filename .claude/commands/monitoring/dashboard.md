---
description: Create monitoring dashboards (Grafana, Datadog, CloudWatch)
argument-hint: [--platform grafana|datadog|cloudwatch|prometheus] [--service service-name] [--metrics custom|default]
model: claude-sonnet-4-5-20250929
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---

Create monitoring dashboard: **${ARGUMENTS:-Grafana with default metrics}**

## What This Command Does

Creates comprehensive monitoring dashboards for observability platforms including:

- **Grafana** - Open-source, beautiful visualizations, flexible data sources
- **Datadog** - Full-stack observability, APM, log management
- **CloudWatch** - Native AWS monitoring, seamless AWS integration
- **Prometheus + Grafana** - Self-hosted, metrics-focused, Kubernetes-native

This command generates dashboard configurations with:

- Application health metrics (request rate, error rate, latency)
- Infrastructure metrics (CPU, memory, disk, network)
- Business metrics (users, transactions, revenue impact)
- Custom service-specific metrics
- Alert annotations and SLO tracking

## Usage Examples

### Create Grafana Dashboard for Microservices

```bash
# Default Grafana dashboard with common metrics
/monitoring:dashboard

# Service-specific dashboard
/monitoring:dashboard --platform grafana --service api-gateway

# Custom metrics dashboard
/monitoring:dashboard --platform grafana --metrics custom
```

### Create Datadog Dashboard for Full-Stack Observability

```bash
# Datadog APM dashboard
/monitoring:dashboard --platform datadog --service user-service

# Infrastructure + APM combined
/monitoring:dashboard --platform datadog
```

### Create CloudWatch Dashboard for AWS Services

```bash
# CloudWatch for Lambda + DynamoDB
/monitoring:dashboard --platform cloudwatch --service lambda-api

# Multi-service CloudWatch dashboard
/monitoring:dashboard --platform cloudwatch
```

### Create Prometheus + Grafana Dashboard

```bash
# Prometheus metrics with Grafana visualization
/monitoring:dashboard --platform prometheus --service kubernetes-cluster
```

## Generated Dashboard Includes

### Application Metrics Panel

- **Request Rate**: Requests per second over time
- **Error Rate**: HTTP 4xx/5xx error percentage
- **Latency Distribution**: P50, P90, P95, P99 latency percentiles
- **Availability**: Uptime percentage and SLO tracking
- **Throughput**: Data processed per second

### Infrastructure Metrics Panel

- **CPU Utilization**: Per instance/container/pod
- **Memory Usage**: Used vs available, with swap
- **Disk I/O**: Read/write IOPS and throughput
- **Network Traffic**: Inbound/outbound bandwidth
- **Container Stats**: Kubernetes pod/container metrics

### Business Metrics Panel

- **Active Users**: Concurrent users and sessions
- **Transaction Volume**: Completed transactions over time
- **Revenue Impact**: Transaction value and revenue tracking
- **Conversion Rate**: Funnel metrics and drop-off points
- **Customer Experience**: User-facing performance metrics

### Alert & Event Panel

- **Active Alerts**: Current firing alerts with severity
- **Deployment Events**: Release markers on timeline
- **Incident Timeline**: Incident start/resolution annotations
- **SLO Status**: Service level objective compliance
- **Anomaly Detection**: AI-detected anomalies highlighted

## Grafana Dashboard Example

```json
{
  "dashboard": {
    "title": "Production Service Health",
    "tags": ["production", "health", "slo"],
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{service}}"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0}
      },
      {
        "id": 2,
        "title": "Error Rate %",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total{status=~\"5..\"}[5m]) / rate(http_requests_total[5m]) * 100",
            "legendFormat": "{{service}}"
          }
        ],
        "alert": {
          "conditions": [
            {
              "evaluator": {"params": [5], "type": "gt"},
              "operator": {"type": "and"},
              "query": {"params": ["A", "5m", "now"]},
              "reducer": {"params": [], "type": "avg"},
              "type": "query"
            }
          ],
          "executionErrorState": "alerting",
          "frequency": "60s",
          "handler": 1,
          "name": "High Error Rate",
          "noDataState": "no_data",
          "notifications": []
        },
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0}
      },
      {
        "id": 3,
        "title": "Response Time (Percentiles)",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.50, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "p50"
          },
          {
            "expr": "histogram_quantile(0.90, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "p90"
          },
          {
            "expr": "histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "p99"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8}
      },
      {
        "id": 4,
        "title": "CPU & Memory",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(process_cpu_seconds_total[5m]) * 100",
            "legendFormat": "CPU %"
          },
          {
            "expr": "process_resident_memory_bytes / 1024 / 1024",
            "legendFormat": "Memory MB"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8}
      },
      {
        "id": 5,
        "title": "SLO Compliance",
        "type": "singlestat",
        "targets": [
          {
            "expr": "sum(rate(http_requests_total{status!~\"5..\"}[30d])) / sum(rate(http_requests_total[30d])) * 100"
          }
        ],
        "thresholds": "99,99.5,99.9",
        "format": "percent",
        "gridPos": {"h": 6, "w": 6, "x": 0, "y": 16}
      },
      {
        "id": 6,
        "title": "Active Users",
        "type": "graph",
        "targets": [
          {
            "expr": "sum(active_users)",
            "legendFormat": "Active Users"
          }
        ],
        "gridPos": {"h": 6, "w": 6, "x": 6, "y": 16}
      }
    ],
    "refresh": "30s",
    "schemaVersion": 27,
    "version": 1
  }
}
```

## Datadog Dashboard Configuration

```json
{
  "title": "Production Service Observability",
  "description": "Full-stack observability for production services",
  "widgets": [
    {
      "definition": {
        "type": "timeseries",
        "requests": [
          {
            "q": "avg:system.cpu.user{env:production}",
            "display_type": "line",
            "style": {
              "palette": "dog_classic",
              "line_type": "solid",
              "line_width": "normal"
            }
          }
        ],
        "title": "CPU Utilization"
      }
    },
    {
      "definition": {
        "type": "query_value",
        "requests": [
          {
            "q": "sum:trace.http.request.hits{service:api,env:production}.as_rate()",
            "aggregator": "avg"
          }
        ],
        "title": "Requests/sec",
        "precision": 2
      }
    },
    {
      "definition": {
        "type": "toplist",
        "requests": [
          {
            "q": "top(avg:trace.http.request.duration.by.resource_service{service:api,env:production} by {resource_name}, 10, 'mean', 'desc')"
          }
        ],
        "title": "Slowest Endpoints"
      }
    },
    {
      "definition": {
        "type": "alert_graph",
        "alert_id": "12345",
        "viz_type": "timeseries",
        "title": "Error Rate Alert Status"
      }
    }
  ],
  "layout_type": "ordered",
  "is_read_only": false,
  "notify_list": [],
  "template_variables": [
    {
      "name": "env",
      "default": "production",
      "prefix": "env"
    },
    {
      "name": "service",
      "default": "*",
      "prefix": "service"
    }
  ]
}
```

## CloudWatch Dashboard Configuration

```json
{
  "DashboardName": "ProductionServiceHealth",
  "DashboardBody": {
    "widgets": [
      {
        "type": "metric",
        "properties": {
          "metrics": [
            ["AWS/Lambda", "Invocations", {"stat": "Sum"}],
            [".", "Errors", {"stat": "Sum"}],
            [".", "Duration", {"stat": "Average"}]
          ],
          "period": 300,
          "stat": "Average",
          "region": "us-east-1",
          "title": "Lambda Metrics",
          "yAxis": {
            "left": {"min": 0}
          }
        }
      },
      {
        "type": "metric",
        "properties": {
          "metrics": [
            ["AWS/DynamoDB", "ConsumedReadCapacityUnits", {"stat": "Sum"}],
            [".", "ConsumedWriteCapacityUnits", {"stat": "Sum"}]
          ],
          "period": 300,
          "stat": "Sum",
          "region": "us-east-1",
          "title": "DynamoDB Capacity"
        }
      },
      {
        "type": "log",
        "properties": {
          "query": "SOURCE '/aws/lambda/my-function'\n| fields @timestamp, @message\n| filter @message like /ERROR/\n| sort @timestamp desc\n| limit 20",
          "region": "us-east-1",
          "title": "Recent Errors"
        }
      }
    ]
  }
}
```

## Prometheus Queries for Common Metrics

```promql
# Request rate (requests per second)
rate(http_requests_total[5m])

# Error rate percentage
rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) * 100

# Latency percentiles
histogram_quantile(0.50, rate(http_request_duration_seconds_bucket[5m]))
histogram_quantile(0.90, rate(http_request_duration_seconds_bucket[5m]))
histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))

# CPU usage
rate(process_cpu_seconds_total[5m]) * 100

# Memory usage
process_resident_memory_bytes / 1024 / 1024

# Active database connections
pg_stat_activity_count

# Cache hit rate
rate(cache_hits_total[5m]) / (rate(cache_hits_total[5m]) + rate(cache_misses_total[5m])) * 100

# Kubernetes pod CPU
rate(container_cpu_usage_seconds_total{pod=~"api-.*"}[5m])

# Queue depth
rabbitmq_queue_messages_ready

# Disk I/O
rate(node_disk_read_bytes_total[5m])
rate(node_disk_written_bytes_total[5m])
```

## Dashboard Best Practices

### Visual Design

- Use consistent color schemes (green = good, yellow = warning, red = critical)
- Group related metrics together in rows/sections
- Use appropriate visualization types (line graphs for time series, gauges for current values)
- Include context with annotations for deployments and incidents
- Add SLO target lines to key metrics

### Metric Selection

- Focus on the 4 golden signals: latency, traffic, errors, saturation
- Include both infrastructure AND business metrics
- Use percentiles (p50, p90, p99) instead of averages for latency
- Add derived metrics (error rate %, cache hit rate %)
- Include capacity metrics (connections, queue depth, disk space)

### Dashboard Organization

- Top row: Critical health indicators (SLO compliance, error rate, availability)
- Second row: Request volume and latency metrics
- Third row: Infrastructure metrics (CPU, memory, disk, network)
- Bottom rows: Detailed breakdowns and business metrics
- Separate dashboard for each major service/component

### Performance Optimization

- Limit time range to reasonable defaults (last 6 hours)
- Use appropriate query intervals (5m for most metrics)
- Avoid excessive panel count (15-20 panels max per dashboard)
- Use template variables for filtering (environment, service, region)
- Enable auto-refresh at sensible intervals (30s-1m)

## Business Value & ROI

### Faster Incident Detection

- **Before**: 15-30 minutes average detection time
- **After**: Sub-1 minute detection with alerting
- **Impact**: Reduce MTTR by 50-70%
- **Value**: $5,000-$50,000 saved per major incident

### Improved System Reliability

- **Visibility**: Real-time health visibility across all services
- **Proactive**: Catch issues before customers are affected
- **SLO Tracking**: Maintain 99.9%+ availability targets
- **Value**: Reduce downtime from hours to minutes

### Development Efficiency

- **Debugging**: Instant visibility into performance issues
- **Optimization**: Data-driven performance improvements
- **Capacity Planning**: Informed scaling decisions
- **Value**: Save 5-10 engineering hours per week

### Executive Reporting

- **Business Metrics**: User activity and transaction volume
- **Revenue Impact**: Correlate performance with revenue
- **Trend Analysis**: Week-over-week and month-over-month trends
- **Value**: Data-driven strategic decisions

## Success Metrics

After implementing monitoring dashboards, track these KPIs:

1. **MTTD (Mean Time To Detect)**: Target < 1 minute
2. **MTTR (Mean Time To Resolve)**: Target 50% reduction
3. **Dashboard Usage**: Engineers check dashboards daily
4. **Alert Accuracy**: 90%+ of alerts are actionable
5. **SLO Compliance**: 99.9%+ availability achieved
6. **False Positive Rate**: < 10% of alerts are false alarms
7. **Coverage**: 100% of critical services monitored
8. **Adoption**: All teams using dashboards for deployments

## Integration with Other Commands

### Development Workflow

- `/dev:implement` - Add instrumentation during feature development
- `/dev:review` - Verify monitoring coverage before PR
- `/monitoring:dashboard` - Create dashboard for new service

### Deployment Workflow

- `/devops:deploy` - Deploy with monitoring enabled
- `/monitoring:dashboard` - Update dashboard with new metrics
- `/monitoring:alerts` - Configure alerts for new service
- `/devops:verify` - Verify metrics are flowing correctly

### Incident Response

- `/monitoring:dashboard` - View real-time service health
- `/monitoring:alerts` - Check which alerts are firing
- `/devops:debug` - Investigate root cause using metrics
- `/devops:rollback` - Rollback if needed
- `/monitoring:runbook` - Follow incident response procedures

### Continuous Improvement

- `/monitoring:slo` - Define SLOs based on dashboard data
- `/monitoring:dashboard` - Refine metrics based on incidents
- `/monitoring:alerts` - Tune alert thresholds to reduce noise

## Example Implementation

```bash
# Install Grafana and Prometheus
docker-compose up -d grafana prometheus

# Create Grafana dashboard via API
curl -X POST http://localhost:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $GRAFANA_API_KEY" \
  -d @dashboard.json

# Configure Prometheus data source
curl -X POST http://localhost:3000/api/datasources \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $GRAFANA_API_KEY" \
  -d '{
    "name": "Prometheus",
    "type": "prometheus",
    "url": "http://prometheus:9090",
    "access": "proxy",
    "isDefault": true
  }'

# Export dashboard for version control
curl http://localhost:3000/api/dashboards/uid/service-health \
  -H "Authorization: Bearer $GRAFANA_API_KEY" \
  > dashboards/service-health.json
```

## Common Dashboard Patterns

### Microservices Dashboard

- Request rate per service
- Error rate per service with breakdown
- Latency percentiles per endpoint
- Inter-service dependency map
- Database query performance

### Kubernetes Dashboard

- Cluster resource utilization
- Pod CPU and memory by namespace
- Node health and capacity
- Persistent volume usage
- HPA (Horizontal Pod Autoscaler) behavior

### Database Dashboard

- Query throughput (queries/sec)
- Slow query log analysis
- Connection pool utilization
- Replication lag (if applicable)
- Cache hit ratio
- Index usage statistics

### API Gateway Dashboard

- Requests per endpoint
- Response time distribution
- Rate limiting metrics
- Authentication success/failure
- Backend service health

## Success Criteria

- Dashboards created for all critical services
- Metrics refresh in real-time (< 30 second lag)
- Visualizations are clear and actionable
- Template variables enable filtering by environment/service
- SLO targets visible on relevant panels
- Deployment events annotated on timeline
- All dashboards version controlled (JSON files)
- Documentation includes dashboard links
- Team trained on dashboard usage
- Dashboards referenced in runbooks

---
**Related Commands**: `/monitoring:alerts`, `/monitoring:slo`, `/monitoring:runbook`, `/devops:monitor`, `/devops:debug`
