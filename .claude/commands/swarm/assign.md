---
description: Manually assign work items to the swarm work queue
argument-hint: "<work-type> --target <id> [--priority critical|high|medium|low] [--domain <domain>]"
model: claude-sonnet-4-5-20250929
allowed-tools: Bash, Read, AskUserQuestion, Task
---

# Assign Work to Swarm

Manually create and assign work items or signals to the autonomous swarm for processing.

## Work Types

| Type | Description | Domain |
|------|-------------|--------|
| `health-check` | Customer health assessment | customer_success |
| `playbook` | Trigger specific playbook | customer_success |
| `rollout-progress` | Progress feature rollout | feature_lifecycle |
| `adoption-report` | Generate adoption report | feature_lifecycle |
| `deprecation-check` | Check deprecation status | feature_lifecycle |
| `competitor-scan` | Scan competitor for changes | market_intel |
| `trend-analysis` | Analyze market trends | market_intel |
| `deployment-validate` | Validate pending deployment | devops |
| `health-refresh` | Batch health refresh | customer_success |

## Execution Steps

### 1. Parse Arguments

Extract from `$ARGUMENTS`:

- **work-type**: Required - type of work to assign
- **--target**: Required - target ID (customer, feature, etc.)
- **--priority**: Optional - critical, high, medium, low (default: medium)
- **--domain**: Optional - override auto-detected domain
- **--data**: Optional - JSON data for work item

### 2. Create Domain Signal

Create a cross-domain signal to trigger swarm action:

```bash
# Create a signal for customer health check
curl -s -X POST "http://localhost:3001/api/v1/cross-domain/signals" \
  -H "Content-Type: application/json" \
  -H "x-workspace-id: default" \
  -d '{
    "signalType": "health_check_requested",
    "sourceDomain": "customer_success",
    "title": "Manual health check request",
    "severity": "medium",
    "signalData": {
      "customerId": "$TARGET_ID",
      "requestedBy": "manual",
      "workType": "$WORK_TYPE"
    },
    "metadata": {
      "priority": "$PRIORITY",
      "source": "swarm:assign"
    }
  }' | jq .
```

### 3. Process the Signal

Trigger signal processing to detect patterns and create work items:

```bash
# Process the created signal (get signal ID from previous response)
curl -s -X POST "http://localhost:3001/api/v1/cross-domain/signals/$SIGNAL_ID/process" \
  -H "x-workspace-id: default" | jq .
```

### 4. Trigger Action (Optional)

If immediate action is required:

```bash
# Trigger a work item action
curl -s -X POST "http://localhost:3001/api/v1/cross-domain/signals/$SIGNAL_ID/trigger" \
  -H "Content-Type: application/json" \
  -H "x-workspace-id: default" \
  -d '{
    "actionType": "work_item"
  }' | jq .
```

### 5. Display Confirmation

```
═══════════════════════════════════════════════════════════
                  WORK ASSIGNED
═══════════════════════════════════════════════════════════

✅ Work Item Created

Signal ID:     sig_xyz789
Type:          health-check
Target:        cust_abc123
Priority:      HIGH
Domain:        customer_success

Processing Status:
  ✓ Signal created
  ✓ Pattern detection run
  ✓ Work item queued

Estimated Processing:
  Queue Position: 3
  Expected Start: ~2 minutes

═══════════════════════════════════════════════════════════

Track with: /swarm:status
View signals: GET /api/v1/cross-domain/signals

═══════════════════════════════════════════════════════════
```

## Examples

### Health Check for Customer

```bash
/swarm:assign health-check --target cust_abc123 --priority high
```

Creates signal:

```bash
curl -s -X POST "http://localhost:3001/api/v1/cross-domain/signals" \
  -H "Content-Type: application/json" \
  -H "x-workspace-id: default" \
  -d '{
    "signalType": "health_check_requested",
    "sourceDomain": "customer_success",
    "title": "Health check for cust_abc123",
    "severity": "high",
    "signalData": {
      "customerId": "cust_abc123",
      "checkType": "full"
    }
  }' | jq .
```

### Trigger Playbook

```bash
/swarm:assign playbook --target cust_abc123 --data '{"playbook_id": "churn-risk-critical"}'
```

Creates signal:

```bash
curl -s -X POST "http://localhost:3001/api/v1/cross-domain/signals" \
  -H "Content-Type: application/json" \
  -H "x-workspace-id: default" \
  -d '{
    "signalType": "playbook_trigger",
    "sourceDomain": "customer_success",
    "title": "Manual playbook trigger: churn-risk-critical",
    "severity": "high",
    "signalData": {
      "customerId": "cust_abc123",
      "playbookId": "churn-risk-critical",
      "trigger": "manual"
    }
  }' | jq .
```

### Competitor Scan

```bash
/swarm:assign competitor-scan --target comp_xyz --priority critical
```

### Deployment Validation

```bash
/swarm:assign deployment-validate --target deploy_xyz --priority critical
```

Creates signal:

```bash
curl -s -X POST "http://localhost:3001/api/v1/cross-domain/signals" \
  -H "Content-Type: application/json" \
  -H "x-workspace-id: default" \
  -d '{
    "signalType": "deployment_validation_requested",
    "sourceDomain": "devops",
    "title": "Validate deployment deploy_xyz",
    "severity": "critical",
    "signalData": {
      "deploymentId": "deploy_xyz",
      "validationType": "full"
    }
  }' | jq .
```

## Signal Type Reference

| Work Type | Signal Type | Domain |
|-----------|-------------|--------|
| health-check | `health_check_requested` | customer_success |
| playbook | `playbook_trigger` | customer_success |
| health-refresh | `batch_health_refresh` | customer_success |
| rollout-progress | `rollout_progression` | feature_lifecycle |
| adoption-report | `adoption_analysis` | feature_lifecycle |
| deprecation-check | `deprecation_assessment` | feature_lifecycle |
| competitor-scan | `competitor_scan` | market_intel |
| trend-analysis | `trend_analysis` | market_intel |
| deployment-validate | `deployment_validation_requested` | devops |

## API Endpoints Used

| Endpoint | Purpose |
|----------|---------|
| `POST /api/v1/cross-domain/signals` | Create signal |
| `POST /api/v1/cross-domain/signals/:id/process` | Process signal |
| `POST /api/v1/cross-domain/signals/:id/trigger` | Trigger action |
| `GET /api/v1/cross-domain/signals/:id` | Get signal status |

## Error Handling

| Error | Resolution |
|-------|------------|
| Invalid work type | Use supported work type |
| Target not found | Verify target ID exists |
| Domain disabled | Enable domain in swarm config |
| Signal creation failed | Check API connection |

---

**Uses**: CrossDomainIntelligence
**Model**: Sonnet (work assignment)
