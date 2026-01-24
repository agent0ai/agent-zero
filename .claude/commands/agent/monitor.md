---
description: Monitor real-time agent activity and performance across all running agents
argument-hint: "[--dashboard] [--filter <agent-type>] [--metrics]"
allowed-tools: ["Read", "Bash", "Grep", "Glob"]
---

# Agent Activity Monitor

Monitor real-time agent activity, track performance metrics, and identify bottlenecks across all running AI agents.

## What This Command Does

This command provides comprehensive real-time monitoring of all active agents in your system:

- **Active Agents**: Show all currently running agents with status
- **Performance Metrics**: Task completion rate, average execution time, success rate
- **Resource Usage**: Token consumption, cost tracking, API usage
- **Queue Status**: Pending tasks, blocked tasks, priority queue
- **Historical Trends**: Performance over time, bottleneck identification

## Monitoring Modes

### 1. Dashboard View (--dashboard)

Launch an interactive real-time dashboard showing:

- Agent status grid with live updates
- Task queue visualization
- Performance graphs (completion rate, avg time)
- Cost tracking and token usage
- Alert notifications for failures

### 2. Filtered View (--filter <agent-type>)

Focus on specific agent types:

- `--filter prompt-engineering` - Only prompt engineering agents
- `--filter gcp` - All GCP-related agents
- `--filter healthcare` - Healthcare domain agents

### 3. Metrics Deep-Dive (--metrics)

Detailed performance metrics:

- Task success/failure rates by agent type
- Average execution time per task category
- Token consumption and cost per agent
- Bottleneck analysis (slow agents, blocked tasks)
- Capacity planning recommendations

## Implementation Steps

1. **Scan Active Agent Processes**
   - Check running Task tool invocations
   - Identify agent types and current tasks
   - Track start times and execution state

2. **Aggregate Performance Metrics**
   - Calculate success rates from completed tasks
   - Track execution times from logs
   - Monitor token usage from API calls
   - Estimate costs based on model usage

3. **Visualize Agent Status**
   - Display agent grid with status indicators
   - Show task queue with priorities
   - Graph performance trends
   - Highlight alerts and anomalies

4. **Generate Recommendations**
   - Identify overloaded agents
   - Suggest scaling opportunities
   - Recommend optimization strategies
   - Alert on performance degradation

## Example Usage

```bash
# Launch real-time dashboard
/agent:monitor --dashboard

# Monitor only GCP agents
/agent:monitor --filter gcp

# Deep-dive metrics analysis
/agent:monitor --metrics

# Continuous monitoring with alerts
/agent:monitor --dashboard --alerts
```

## Monitoring Outputs

### Agent Status Grid

```
┌─────────────────────────────────────────────────┐
│ AGENT STATUS (Last updated: 2024-01-15 14:30)  │
├─────────────────────────────────────────────────┤
│ 🟢 gcp-infrastructure-architect    [ACTIVE]     │
│    Task: Terraform configuration                │
│    Runtime: 2m 34s                              │
│    Progress: 65%                                │
│                                                 │
│ 🟢 code-reviewer                   [ACTIVE]     │
│    Task: Security audit                         │
│    Runtime: 1m 12s                              │
│    Progress: 40%                                │
│                                                 │
│ 🟡 prompt-engineering              [IDLE]       │
│    Last task completed: 5m ago                  │
│                                                 │
│ 🔴 devops-github-docker            [FAILED]     │
│    Error: Docker build timeout                  │
│    Failed: 2m ago                               │
└─────────────────────────────────────────────────┘
```

### Performance Metrics

```
📊 AGENT PERFORMANCE SUMMARY
════════════════════════════════════════════════
Total Active Agents:        4
Tasks Completed (24h):      127
Success Rate:               94.5%
Avg Execution Time:         3m 24s
Token Consumption (24h):    1.2M tokens
Estimated Cost (24h):       $12.50

Top Performers:
  1. code-reviewer          98% success, 2m avg
  2. gcp-cost-optimizer     96% success, 4m avg
  3. accessibility-auditor  95% success, 5m avg

Needs Attention:
  ⚠️  devops-deploy         78% success (timeouts)
  ⚠️  playwright-test       82% success (flaky tests)
════════════════════════════════════════════════
```

## Business Value

**ROI**: $60,000/year in productivity gains

- **Faster Issue Resolution**: Identify agent failures immediately ($20K/year)
- **Capacity Optimization**: Right-size agent allocation ($15K/year)
- **Cost Tracking**: Monitor and optimize token/API usage ($15K/year)
- **Performance Improvement**: Identify and fix bottlenecks ($10K/year)

**Time Savings**: 5 hours/week on debugging and optimization

## Success Metrics

- Agent uptime > 99%
- Mean time to detect issues < 30 seconds
- Mean time to resolution < 5 minutes
- 90% of tasks complete within SLA
- Token cost variance < 10% week-over-week

---

*This command provides comprehensive visibility into your multi-agent system, enabling proactive management and optimization.*
