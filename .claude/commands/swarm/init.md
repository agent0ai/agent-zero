---
description: Initialize an autonomous swarm for product management operations
argument-hint: "<product-name> [--domains feature-lifecycle,market-intel,customer-success,devops]"
model: claude-sonnet-4-5-20250929
allowed-tools: Bash, Read, Write, AskUserQuestion, Task
---

# Initialize Autonomous Swarm

Initialize a new autonomous swarm for managing product operations with multi-agent coordination.

## Execution Steps

### 1. Parse Configuration

Extract from arguments:

- **Product Name**: Required - the product to manage (from `$ARGUMENTS`)
- **Domains**: Optional - comma-separated list of domains to activate
  - `feature-lifecycle` - Feature rollouts, adoption tracking, deprecation
  - `market-intel` - Competitor watching, trend analysis
  - `customer-success` - Health monitoring, playbook execution
  - `devops` - Deployment governance, auto-rollback

Default: All domains enabled

### 2. Validate Prerequisites

Run pre-flight checks via API:

```bash
# Check backend health
curl -s -X GET "http://localhost:3001/api/health" | jq .

# Check swarm orchestrator health
curl -s -X GET "http://localhost:3001/api/v1/swarm/health" \
  -H "x-workspace-id: default" | jq .

# Check cross-domain intelligence service
curl -s -X GET "http://localhost:3001/api/v1/cross-domain/health" \
  -H "x-workspace-id: default" | jq .

# Check knowledge service
curl -s -X GET "http://localhost:3001/api/v1/swarm-knowledge/health" \
  -H "x-workspace-id: default" | jq .
```

### 3. Create Swarm Configuration

First create a swarm config with colonies for each domain:

```bash
# Create swarm configuration
curl -s -X POST "http://localhost:3001/api/v1/swarm/configs" \
  -H "Content-Type: application/json" \
  -H "x-workspace-id: default" \
  -d '{
    "name": "[Product Name] Swarm Config",
    "description": "Autonomous product management swarm for [Product Name]",
    "colonies": [
      {
        "id": "customer-success-colony",
        "name": "Customer Success Colony",
        "purpose": "customer_success",
        "agents": [
          {"agentType": "health-monitor", "displayName": "Health Monitor", "capabilities": ["health-scoring", "alert-generation"]},
          {"agentType": "playbook-engine", "displayName": "Playbook Engine", "capabilities": ["playbook-execution", "intervention"]}
        ],
        "maxConcurrent": 4,
        "priority": 9
      },
      {
        "id": "feature-lifecycle-colony",
        "name": "Feature Lifecycle Colony",
        "purpose": "feature_lifecycle",
        "agents": [
          {"agentType": "rollout-coordinator", "displayName": "Rollout Coordinator", "capabilities": ["staged-rollout", "adoption-tracking"]},
          {"agentType": "adoption-tracker", "displayName": "Adoption Tracker", "capabilities": ["usage-analysis", "feedback-collection"]},
          {"agentType": "deprecation-manager", "displayName": "Deprecation Manager", "capabilities": ["deprecation-tracking", "migration-support"]}
        ],
        "maxConcurrent": 3,
        "priority": 7
      },
      {
        "id": "market-intelligence-colony",
        "name": "Market Intelligence Colony",
        "purpose": "market_intelligence",
        "agents": [
          {"agentType": "competitor-watcher", "displayName": "Competitor Watcher", "capabilities": ["competitor-monitoring", "alert-generation"]},
          {"agentType": "trend-analyzer", "displayName": "Trend Analyzer", "capabilities": ["trend-analysis", "reporting"]}
        ],
        "maxConcurrent": 2,
        "priority": 6
      },
      {
        "id": "devops-pipeline-colony",
        "name": "DevOps Pipeline Colony",
        "purpose": "devops_pipeline",
        "agents": [
          {"agentType": "deployment-guard", "displayName": "Deployment Guard", "capabilities": ["deployment-validation", "gate-enforcement"]},
          {"agentType": "rollback-sentinel", "displayName": "Rollback Sentinel", "capabilities": ["error-detection", "auto-rollback"]}
        ],
        "maxConcurrent": 3,
        "priority": 10
      }
    ],
    "maxConcurrentAgents": 12,
    "autoScaling": true,
    "autonomyLevel": "high",
    "checkpointIntervalMs": 60000,
    "enableLearning": true,
    "enableCrossDomainIntelligence": true
  }' | jq .
```

Save the returned `CONFIG_ID` for the next step.

### 4. Initialize Swarm Instance

Create a swarm instance using the config:

```bash
# Initialize swarm with config
curl -s -X POST "http://localhost:3001/api/v1/swarm/initialize" \
  -H "Content-Type: application/json" \
  -H "x-workspace-id: default" \
  -d '{
    "name": "[Product Name] Swarm Instance",
    "configId": "$CONFIG_ID",
    "initialContext": {
      "product": "[Product Name]",
      "environment": "development",
      "autonomyTarget": 0.90
    }
  }' | jq .
```

Save the returned `SWARM_ID` for tracking.

### 5. Verify Cross-Domain Patterns

Verify the 6 pre-registered patterns are available:

```bash
# Verify patterns registered
curl -s -X GET "http://localhost:3001/api/v1/cross-domain/patterns" \
  -H "x-workspace-id: default" | jq '.data | length'
```

Expected patterns:

- `churn-risk-critical` - Customer health correlation
- `adoption-ux-issue` - Feature adoption problems
- `competitive-threat` - Competitor activity
- `deployment-incident` - DevOps correlation
- `expansion-opportunity` - Growth signals
- `feature-deprecation-impact` - Deprecation tracking

### 6. Start Learning Loops

Initialize the knowledge service learning loops:

```bash
# Start learning loops for continuous improvement
curl -s -X POST "http://localhost:3001/api/v1/swarm-knowledge/loops/start" \
  -H "x-workspace-id: default" | jq .
```

### 7. Display Initialization Summary

```
═══════════════════════════════════════════════════════════
                 SWARM INITIALIZED
═══════════════════════════════════════════════════════════

✅ Swarm Initialized Successfully

Config ID:  [CONFIG_ID]
Swarm ID:   [SWARM_ID]
Product:    [Product Name]

Domains Activated:
  ✓ Customer Success (2 agent types)
    - health-monitor
    - playbook-engine
  ✓ Feature Lifecycle (3 agent types)
    - rollout-coordinator
    - adoption-tracker
    - deprecation-manager
  ✓ Market Intelligence (2 agent types)
    - competitor-watcher
    - trend-analyzer
  ✓ DevOps Pipeline (2 agent types)
    - deployment-guard
    - rollback-sentinel

Cross-Domain Patterns: 6 registered
  • churn-risk-critical
  • adoption-ux-issue
  • competitive-threat
  • deployment-incident
  • expansion-opportunity
  • feature-deprecation-impact

Learning Loops Started:
  • Intervention Feedback (daily)
  • Playbook Analysis (weekly)
  • Pattern Extraction (daily)

Settings:
  Autonomy Target:       90%
  Checkpoint Interval:   60 seconds
  Max Concurrent Agents: 12
  Auto-Scaling:          Enabled

═══════════════════════════════════════════════════════════

Next Steps:
  1. /swarm:status - View current state
  2. /swarm:assign - Add work items
  3. /swarm:report - Generate activity report

API Endpoints:
  Orchestrator:  POST /api/v1/swarm/*
  Cross-Domain:  /api/v1/cross-domain/*
  Knowledge:     /api/v1/swarm-knowledge/*

═══════════════════════════════════════════════════════════
```

## Backend Services Used

| Service | Endpoint | Purpose |
|---------|----------|---------|
| SwarmOrchestrator | `POST /api/v1/swarm/configs` | Create config |
| SwarmOrchestrator | `POST /api/v1/swarm/initialize` | Initialize instance |
| CrossDomainIntelligence | `GET /api/v1/cross-domain/patterns` | Verify patterns |
| SwarmKnowledgeService | `POST /api/v1/swarm-knowledge/loops/start` | Start learning |

## Error Handling

| Error | Resolution |
|-------|------------|
| Backend not reachable | Start backend server: `npm run dev` |
| Database not ready | Run database migrations |
| Config creation failed | Check colonies format |
| Already initialized | Use existing swarm or delete first |

---

**Uses**: SwarmOrchestrator, CrossDomainIntelligence, SwarmKnowledgeService
**Model**: Sonnet (initialization orchestration)
