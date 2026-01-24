---
description: Generate comprehensive swarm activity and performance report
argument-hint: "[--period daily|weekly|monthly] [--format text|json|markdown] [--export <file>]"
model: claude-sonnet-4-5-20250929
allowed-tools: Bash, Read, Write, Task
---

# Swarm Activity Report

Generate detailed reports on swarm operations, decision metrics, and performance analytics.

## Report Types

| Period | Coverage | Use Case |
|--------|----------|----------|
| `daily` | Last 24 hours | Daily standups, quick review |
| `weekly` | Last 7 days | Team meetings, trend analysis |
| `monthly` | Last 30 days | Executive review, planning |

## Execution Steps

### 1. Parse Arguments

Extract from `$ARGUMENTS`:

- **--period**: daily (default), weekly, monthly
- **--format**: text (default), json, markdown
- **--export**: Optional file path for export

Set period days:

- daily = 1
- weekly = 7
- monthly = 30

### 2. Collect Cross-Domain Statistics

Get signal processing metrics:

```bash
# Get signal statistics
curl -s -X GET "http://localhost:3001/api/v1/cross-domain/stats?timeWindowDays=$PERIOD_DAYS" \
  -H "x-workspace-id: default" | jq .
```

### 3. Collect Learning Metrics

Get decision and learning analytics:

```bash
# Get learning metrics
curl -s -X GET "http://localhost:3001/api/v1/swarm-knowledge/metrics?periodDays=$PERIOD_DAYS" \
  -H "x-workspace-id: default" | jq .

# Get decision accuracy analysis
curl -s -X GET "http://localhost:3001/api/v1/swarm-knowledge/metrics/decisions?periodDays=$PERIOD_DAYS" \
  -H "x-workspace-id: default" | jq .
```

### 4. Get Pattern Information

List active patterns and their status:

```bash
# Get registered patterns
curl -s -X GET "http://localhost:3001/api/v1/cross-domain/patterns" \
  -H "x-workspace-id: default" | jq .
```

### 5. Get Recent Signals

List signals for the period:

```bash
# Get signals for period
curl -s -X GET "http://localhost:3001/api/v1/cross-domain/signals?limit=100" \
  -H "x-workspace-id: default" | jq .
```

### 6. Get Knowledge Activity

List knowledge entries created:

```bash
# Get recent knowledge entries
curl -s -X GET "http://localhost:3001/api/v1/swarm-knowledge?limit=20" \
  -H "x-workspace-id: default" | jq .
```

### 7. Generate Report

Format and display comprehensive report:

```
═══════════════════════════════════════════════════════════════════════════════
                         SWARM ACTIVITY REPORT
                         Period: [PERIOD] (Last [DAYS] days)
═══════════════════════════════════════════════════════════════════════════════

Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)
Workspace: default

───────────────────────────────────────────────────────────────────────────────
EXECUTIVE SUMMARY
───────────────────────────────────────────────────────────────────────────────

🟢 Operational Status: HEALTHY

Key Metrics:
  Decision Accuracy:     [%] (Target: 85%)
  Autonomy Rate:         [%] (Target: 90%)
  False Positive Rate:   [%] (Target: <10%)

───────────────────────────────────────────────────────────────────────────────
SIGNAL ACTIVITY
───────────────────────────────────────────────────────────────────────────────

Total Signals:          [count]
├── By Severity:
│   ├── Critical:       [count]
│   ├── High:           [count]
│   ├── Medium:         [count]
│   ├── Low:            [count]
│   └── Info:           [count]
│
├── By Domain:
│   ├── Customer Success:    [count]
│   ├── Feature Lifecycle:   [count]
│   ├── Market Intel:        [count]
│   └── DevOps:              [count]
│
└── Actions Triggered:  [count]

───────────────────────────────────────────────────────────────────────────────
DECISION ANALYTICS
───────────────────────────────────────────────────────────────────────────────

Total Decisions:        [count]

By Domain:
  ├── Customer Success:    [count] ([%])
  ├── Feature Lifecycle:   [count] ([%])
  ├── Market Intelligence: [count] ([%])
  └── DevOps Pipeline:     [count] ([%])

Decision Quality:
  ├── Success Rate:        [%]
  ├── Override Rate:       [%]
  └── Avg Confidence:      [%]

───────────────────────────────────────────────────────────────────────────────
LEARNING METRICS
───────────────────────────────────────────────────────────────────────────────

Decision Performance:
  ├── Accuracy:            [%]
  ├── Autonomy Rate:       [%]
  ├── False Positive Rate: [%]
  ├── False Negative Rate: [%]
  └── Avg Time to Outcome: [days] days

Playbook Effectiveness:
  ├── Total Executions:    [count]
  ├── Success Rate:        [%]
  └── Avg Completion Time: [hours] hours

Intervention Metrics:
  ├── Total Interventions: [count]
  ├── Successful Outcomes: [count]
  ├── Pending Outcomes:    [count]
  └── Avg Response Time:   [hours] hours

Knowledge Base:
  ├── Total Entries:       [count]
  ├── Created This Period: [count]
  ├── Avg Usefulness:      [score]
  └── Entries Refined:     [count]

───────────────────────────────────────────────────────────────────────────────
PATTERN ACTIVITY
───────────────────────────────────────────────────────────────────────────────

Registered Patterns:    6
Patterns Enabled:       6

Pattern                         Matches   Actions
─────────────────────────────────────────────────
churn-risk-critical             [count]   [count]
adoption-ux-issue               [count]   [count]
competitive-threat              [count]   [count]
deployment-incident             [count]   [count]
expansion-opportunity           [count]   [count]
feature-deprecation-impact      [count]   [count]

───────────────────────────────────────────────────────────────────────────────
RECOMMENDATIONS
───────────────────────────────────────────────────────────────────────────────

Based on the metrics analysis:

[Recommendations from decision accuracy analysis]

───────────────────────────────────────────────────────────────────────────────

Report Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)
Next Report: [calculated based on period]

═══════════════════════════════════════════════════════════════════════════════
```

### 8. Export Report (if --export)

Save report to file:

```bash
# Export based on format
if [ "$FORMAT" = "json" ]; then
  # Export as JSON
  curl -s -X GET "http://localhost:3001/api/v1/swarm-knowledge/metrics?periodDays=$PERIOD_DAYS" \
    -H "x-workspace-id: default" > "$EXPORT_FILE"
elif [ "$FORMAT" = "markdown" ]; then
  # Export as Markdown (formatted report)
  echo "# Swarm Activity Report" > "$EXPORT_FILE"
  echo "" >> "$EXPORT_FILE"
  echo "Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$EXPORT_FILE"
  # ... append report content
fi

echo "Report exported to: $EXPORT_FILE"
```

## API Endpoints Used

| Endpoint | Purpose |
|----------|---------|
| `GET /api/v1/cross-domain/stats` | Signal statistics |
| `GET /api/v1/cross-domain/patterns` | Pattern registry |
| `GET /api/v1/cross-domain/signals` | Signal list |
| `GET /api/v1/swarm-knowledge/metrics` | Learning metrics |
| `GET /api/v1/swarm-knowledge/metrics/decisions` | Decision accuracy |
| `GET /api/v1/swarm-knowledge` | Knowledge entries |

## JSON Export Format

```json
{
  "reportType": "daily",
  "generatedAt": "2025-01-15T16:00:00Z",
  "periodDays": 1,
  "signals": {
    "total": 100,
    "bySeverity": { ... },
    "byDomain": { ... },
    "actionsTriggered": 45
  },
  "learning": {
    "decisionAccuracy": 94.2,
    "autonomyRate": 91.0,
    "falsePositiveRate": 3.8,
    "playbook": { ... },
    "interventions": { ... },
    "knowledge": { ... }
  },
  "patterns": {
    "registered": 6,
    "enabled": 6,
    "activity": { ... }
  },
  "recommendations": [ ... ]
}
```

## Error Handling

| Error | Resolution |
|-------|------------|
| No data for period | Check swarm was running |
| Export path invalid | Use valid file path |
| API unavailable | Check backend is running |

---

**Uses**: CrossDomainIntelligence, SwarmKnowledgeService
**Model**: Sonnet (report generation)
