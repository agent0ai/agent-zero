---
description: View current swarm state, agent status, and operational metrics
argument-hint: "[--swarm-id <id>] [--detailed]"
model: claude-sonnet-4-5-20250929
allowed-tools: Bash, Read, Task
---

# Swarm Status

Display comprehensive status of the autonomous swarm including instances, work queue, and health metrics.

## Execution Steps

### 1. Query Swarm Instances

Get active swarm instances:

```bash
# List all swarm instances
curl -s -X GET "http://localhost:3001/api/v1/swarm/instances?limit=10" \
  -H "x-workspace-id: default" | jq .

# If --swarm-id provided, get specific instance
curl -s -X GET "http://localhost:3001/api/v1/swarm/instances/$SWARM_ID" \
  -H "x-workspace-id: default" | jq .
```

### 2. Query Service Health

Check overall system health:

```bash
# Check swarm orchestrator health
curl -s -X GET "http://localhost:3001/api/v1/swarm/health" \
  -H "x-workspace-id: default" | jq .

# Check cross-domain intelligence health
curl -s -X GET "http://localhost:3001/api/v1/cross-domain/health" \
  -H "x-workspace-id: default" | jq .

# Check knowledge service health
curl -s -X GET "http://localhost:3001/api/v1/swarm-knowledge/health" \
  -H "x-workspace-id: default" | jq .
```

### 3. Get Work Items (if swarm-id provided)

List pending work items for a swarm:

```bash
# Get work items for swarm
curl -s -X GET "http://localhost:3001/api/v1/swarm/instances/$SWARM_ID/work-items?limit=20" \
  -H "x-workspace-id: default" | jq .
```

### 4. Get Cross-Domain Signal Statistics

Retrieve signal processing stats:

```bash
# Get signal statistics for last 30 days
curl -s -X GET "http://localhost:3001/api/v1/cross-domain/stats?timeWindowDays=30" \
  -H "x-workspace-id: default" | jq .
```

### 5. Get Registered Patterns

List active correlation patterns:

```bash
# Get all registered patterns
curl -s -X GET "http://localhost:3001/api/v1/cross-domain/patterns" \
  -H "x-workspace-id: default" | jq .
```

### 6. Get Recent Signals

List recent domain signals:

```bash
# Get recent signals (last 20)
curl -s -X GET "http://localhost:3001/api/v1/cross-domain/signals?limit=20" \
  -H "x-workspace-id: default" | jq '.data[] | {type: .signalType, domain: .sourceDomain, severity: .severity, triggered: .actionTriggered}'
```

### 7. Get Learning Metrics

Retrieve learning and decision metrics:

```bash
# Get learning metrics for last 30 days
curl -s -X GET "http://localhost:3001/api/v1/swarm-knowledge/metrics?periodDays=30" \
  -H "x-workspace-id: default" | jq .

# Get decision accuracy analysis
curl -s -X GET "http://localhost:3001/api/v1/swarm-knowledge/metrics/decisions?periodDays=30" \
  -H "x-workspace-id: default" | jq .
```

### 8. Display Status Dashboard

Format and display comprehensive status:

```
═══════════════════════════════════════════════════════════
                    SWARM STATUS
═══════════════════════════════════════════════════════════

Workspace:    default
Timestamp:    2025-01-15T14:30:00Z

─────────────────────────────────────────────────────────────
SWARM INSTANCES
─────────────────────────────────────────────────────────────

ID                                    Status    Runtime    Work Items
────────────────────────────────────────────────────────────────────────
swarm_abc123                          🟢 RUNNING   4h 23m     12/15
swarm_def456                          ⏸️ PAUSED    1h 15m      3/8

─────────────────────────────────────────────────────────────
SERVICES HEALTH
─────────────────────────────────────────────────────────────

Swarm Orchestrator:         🟢 Healthy
  Capabilities:
    ✓ config_management
    ✓ swarm_lifecycle
    ✓ pause_resume
    ✓ checkpointing

Cross-Domain Intelligence:  🟢 Healthy
  Patterns Registered:      6
  Patterns Enabled:         6

Knowledge Service:          🟢 Healthy
  Capabilities:
    ✓ knowledge_crud
    ✓ semantic_search
    ✓ execution_learning
    ✓ decision_learning
    ✓ pattern_extraction
    ✓ metrics_calculation
    ✓ learning_loops

─────────────────────────────────────────────────────────────
CROSS-DOMAIN PATTERNS
─────────────────────────────────────────────────────────────

Pattern                         Status    Min Confidence
──────────────────────────────────────────────────────────────
churn-risk-critical             🟢 On     70%
adoption-ux-issue               🟢 On     70%
competitive-threat              🟢 On     70%
deployment-incident             🟢 On     70%
expansion-opportunity           🟢 On     70%
feature-deprecation-impact      🟢 On     70%

─────────────────────────────────────────────────────────────
SIGNAL STATISTICS (30 days)
─────────────────────────────────────────────────────────────

Total Signals:        [count]
├── By Severity:
│   ├── Critical:     [count]
│   ├── High:         [count]
│   ├── Medium:       [count]
│   ├── Low:          [count]
│   └── Info:         [count]
│
├── By Domain:
│   ├── Customer Success:    [count]
│   ├── Feature Lifecycle:   [count]
│   ├── Market Intel:        [count]
│   └── DevOps:              [count]
│
└── Actions Triggered: [count]

─────────────────────────────────────────────────────────────
LEARNING METRICS (30 days)
─────────────────────────────────────────────────────────────

Decision Performance:
  ├── Accuracy:           [%]  (Target: 85%)
  ├── Autonomy Rate:      [%]  (Target: 90%)
  ├── False Positive Rate: [%] (Target: <10%)
  └── Override Rate:      [%]

Knowledge Base:
  ├── Total Entries:      [count]
  ├── Created This Period: [count]
  └── Avg Usefulness:     [score]

─────────────────────────────────────────────────────────────
RECENT SIGNALS (Last 5)
─────────────────────────────────────────────────────────────

Type                          Domain              Severity  Triggered
────────────────────────────────────────────────────────────────────────
health_score_drop             customer_success    critical  ✓
deployment_error              devops_pipeline     high      ✓
competitor_launch             market_intelligence medium    ✗
...

═══════════════════════════════════════════════════════════

Commands:
  /swarm:assign  - Add work items
  /swarm:pause   - Pause operations
  /swarm:report  - Full activity report

═══════════════════════════════════════════════════════════
```

### 9. Detailed Output (if --detailed)

If `--detailed` flag provided, also show:

```bash
# Get swarm configs
curl -s -X GET "http://localhost:3001/api/v1/swarm/configs?limit=5" \
  -H "x-workspace-id: default" | jq .

# Get all knowledge entries
curl -s -X GET "http://localhost:3001/api/v1/swarm-knowledge?limit=10" \
  -H "x-workspace-id: default" | jq .

# Get learning loop status
curl -s -X GET "http://localhost:3001/api/v1/swarm-knowledge/loops/status" \
  -H "x-workspace-id: default" | jq .
```

## API Endpoints Used

| Endpoint | Purpose |
|----------|---------|
| `GET /api/v1/swarm/instances` | List swarm instances |
| `GET /api/v1/swarm/instances/:id` | Get specific instance |
| `GET /api/v1/swarm/instances/:id/work-items` | Get work queue |
| `GET /api/v1/swarm/health` | Orchestrator health |
| `GET /api/v1/cross-domain/health` | Cross-domain health |
| `GET /api/v1/cross-domain/stats` | Signal statistics |
| `GET /api/v1/cross-domain/patterns` | Pattern registry |
| `GET /api/v1/cross-domain/signals` | Recent signals |
| `GET /api/v1/swarm-knowledge/health` | Knowledge service health |
| `GET /api/v1/swarm-knowledge/metrics` | Learning metrics |
| `GET /api/v1/swarm-knowledge/metrics/decisions` | Decision accuracy |

## Error Handling

| Error | Resolution |
|-------|------------|
| No active swarm | Run `/swarm:init` first |
| Services unavailable | Check backend is running |
| Database connection failed | Verify database connectivity |

---

**Uses**: SwarmOrchestrator, CrossDomainIntelligence, SwarmKnowledgeService
**Model**: Sonnet (status aggregation)
