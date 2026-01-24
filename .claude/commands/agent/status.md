---
description: Check status and performance metrics for all agents or a specific agent type
argument-hint: "[agent-type] [--history] [--json]"
allowed-tools: ["Read", "Bash", "Grep"]
---

# Agent Status Check

Get current status, health, and performance metrics for AI agents in your system.

## What This Command Does

Quickly check the health and status of your AI agent fleet:

- **Current State**: Active, idle, failed, or disabled
- **Recent Activity**: Last 10 tasks executed
- **Performance Stats**: Success rate, avg execution time, cost
- **Health Indicators**: Error rates, timeout frequency, resource usage

## Usage

```bash
# Check all agents
/agent:status

# Check specific agent type
/agent:status gcp-infrastructure-architect

# View historical performance
/agent:status code-reviewer --history

# Export to JSON for monitoring systems
/agent:status --json
```

## Status Output Format

```
🤖 AGENT STATUS REPORT
════════════════════════════════════════════════════════════════════

📊 gcp-infrastructure-architect
   Status:              🟢 HEALTHY
   Last Active:         2 minutes ago
   Tasks Today:         15
   Success Rate:        93.3% (14/15)
   Avg Execution Time:  4m 23s
   Token Usage:         145K tokens
   Estimated Cost:      $1.45

   Recent Tasks:
   ✅ Terraform configuration for Cloud SQL         (3m 45s ago)
   ✅ VPC network setup with firewall rules        (12m ago)
   ⚠️  GKE cluster deployment (timeout)            (18m ago)
   ✅ Cloud Storage bucket with CDN                (25m ago)

📊 code-reviewer
   Status:              🟢 ACTIVE
   Current Task:        Security audit of auth system
   Started:             45 seconds ago
   Progress:            ~30%
   Tasks Today:         23
   Success Rate:        100% (23/23)
   Avg Execution Time:  2m 12s

📊 playwright-test-architect
   Status:              🟡 DEGRADED
   Last Active:         15 minutes ago
   Tasks Today:         8
   Success Rate:        75% (6/8) ⚠️
   Recent Failures:     2 (flaky test detection)
   Health Warning:      Below 90% success threshold

════════════════════════════════════════════════════════════════════
Total Agents: 12 active, 3 idle, 1 degraded, 0 failed
System Health: 🟢 HEALTHY (94% overall success rate)
```

## JSON Export Format

```json
{
  "timestamp": "2024-01-15T14:30:00Z",
  "agents": [
    {
      "type": "gcp-infrastructure-architect",
      "status": "healthy",
      "last_active": "2m ago",
      "tasks_today": 15,
      "success_rate": 0.933,
      "avg_execution_time_seconds": 263,
      "token_usage": 145000,
      "estimated_cost_usd": 1.45
    }
  ],
  "system_health": {
    "overall_success_rate": 0.94,
    "active_agents": 12,
    "idle_agents": 3,
    "degraded_agents": 1,
    "failed_agents": 0
  }
}
```

## Health Status Indicators

- 🟢 **HEALTHY**: >90% success rate, no recent failures
- 🟡 **DEGRADED**: 70-90% success rate or repeated timeouts
- 🔴 **FAILED**: <70% success rate or critical error
- ⚫ **IDLE**: No activity in last 30 minutes
- 🔵 **ACTIVE**: Currently executing a task

---

*Quick health checks help identify issues before they impact productivity.*
