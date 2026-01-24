---
description: List available and installed MCP servers with connection status, capabilities, and health metrics
argument-hint: [--detailed] [--monitor] [--test-connections] [--filter <category>] [--format <table|json|markdown>]
model: claude-3-5-haiku-20241022
allowed-tools:
  - Bash
  - Read
  - Grep
---

# MCP Server List & Status Command

## Overview

Display comprehensive inventory of available and installed Model Context Protocol servers. Includes connection status, capabilities, authentication status, usage metrics, and health diagnostics.

## What This Command Shows

### Default View (Quick Status)

```
MCP Servers Installed (4 servers, 3 connected)

✅ GITHUB                       | Connected | 2 repos | 47 ops | Since: 2 hours
✅ POSTGRES                     | Connected | prod_db | 12 ops | Since: 4 days
✅ SLACK                        | Connected | #general | 8 ops  | Since: 12 hours
⚠️  N8N                         | Degraded  | API timeout | 15 ops | Since: 8 hours
❌ GOOGLE-DRIVE                 | Not Installed | - | - | -

MCP Servers Available for Installation (8 servers)

💾 STRIPE                       | Payment processing | OAuth + API Key
💾 NOTION                       | Document management | API Token
💾 LINEAR                       | Issue tracking | API Key
💾 AWS-S3                       | Object storage | AWS Credentials
```

### Detailed View

```
INSTALLED MCP SERVERS
═════════════════════════════════════════════════════════════════

Server: GITHUB
├── Status: Connected ✅
├── Version: 1.2.0
├── Authenticated: Yes (@username)
├── Scopes: repo, read:user, read:org
├── Uptime: 99.8% (last 7 days)
├── Connected Since: 2025-11-25 14:30:00 (2 hours 15 mins)
├── Last Activity: 2025-11-25 16:30:00 (just now)
├── Rate Limit: 60/60 requests remaining
├── Available Operations: 47
│   ├── get-repository
│   ├── list-repositories
│   ├── create-issue
│   ├── create-pull-request
│   ├── [43 more operations]
├── Repositories: 42
│   ├── prompt-blueprint (Owner)
│   ├── ai-agents (Contributor)
│   └── [40 more repositories]
├── Performance Metrics
│   ├── Avg Response Time: 245ms
│   ├── Error Rate: 0.01%
│   ├── Requests Today: 247
│   └── Cache Hit Rate: 87%
├── Configuration File: ~/.mcp/config/github.json
└── Integration Points
    ├── /dev:create-pr (GitHub MCP required)
    ├── /agent:route (with GitHub tasks)
    └── /workflow:create (can use GitHub operations)

Server: POSTGRESQL
├── Status: Connected ✅
├── Version: 1.1.3 (PostgreSQL 13.8)
├── Authenticated: Yes (analytics_user)
├── Connection: postgres.example.com:5432 / production_db
├── SSL/TLS: Enabled
├── Uptime: 100% (last 7 days)
├── Connected Since: 2025-11-19 10:00:00 (6 days 6 hours)
├── Last Activity: 2025-11-25 16:31:00 (just now)
├── Available Operations: 12
│   ├── execute-query
│   ├── get-table-schema
│   ├── get-column-statistics
│   ├── [9 more operations]
├── Database Info
│   ├── Tables: 47
│   ├── Functions: 12
│   ├── Views: 8
│   ├── Total Rows: 2,847,394
│   └── Database Size: 8.4 GB
├── Performance Metrics
│   ├── Avg Query Time: 127ms
│   ├── Max Query Time: 3.2s
│   ├── Slow Queries (>1s): 3
│   ├── Connections Used: 2/10
│   └── Cache Hit Rate: 92%
├── Configuration File: ~/.mcp/config/postgres.json (encrypted)
└── Integration Points
    ├── /db:query (uses PostgreSQL MCP)
    ├── /zoho:sync-data (source: postgres-mcp)
    └── /workflow:create (data source)

Server: SLACK
├── Status: Connected ✅
├── Version: 1.0.2
├── Authenticated: Yes (Workspace: example-workspace)
├── Bot Token: xoxb-••••••••••••••••••••
├── Uptime: 99.5% (last 7 days)
├── Connected Since: 2025-11-25 04:30:00 (12 hours 1 min)
├── Last Activity: 2025-11-25 16:32:00 (just now)
├── Available Operations: 8
│   ├── send-message
│   ├── list-channels
│   ├── create-channel
│   ├── [5 more operations]
├── Workspace Info
│   ├── Channels: 34
│   ├── Members: 127
│   ├── Integrations: 8
│   └── Plan: Pro
├── Performance Metrics
│   ├── Avg Response Time: 89ms
│   ├── Error Rate: 0%
│   ├── Messages Sent Today: 12
│   └── API Calls Today: 145
├── Configuration File: ~/.mcp/config/slack.json (encrypted)
└── Integration Points
    ├── /agent:route (Slack notifications)
    └── /workflow:create (Slack actions)

Server: N8N
├── Status: Degraded ⚠️
├── Version: 1.15.0
├── Authenticated: Yes
├── Server URL: https://n8n.example.com
├── Uptime: 87.2% (last 7 days)
├── Connected Since: 2025-11-19 08:00:00 (6 days 8 hours)
├── Last Activity: 2025-11-25 14:15:00 (2 hours 17 mins)
├── Last Error: "API timeout (2s)" at 2025-11-25 14:15:00
├── Available Operations: 15
│   ├── list-workflows
│   ├── trigger-workflow
│   ├── create-workflow
│   ├── [12 more operations]
├── Workflow Info
│   ├── Total Workflows: 23
│   ├── Active: 19
│   ├── Paused: 4
│   └── Recent Executions: 156 (last 7 days)
├── Performance Metrics
│   ├── Avg Response Time: 1.2s ⚠️ (elevated)
│   ├── Error Rate: 2.4% ⚠️ (elevated)
│   ├── Requests Today: 67
│   └── Failed Requests: 2
├── Configuration File: ~/.mcp/config/n8n.json (encrypted)
├── Recommendation: Check n8n server health
│   └── Command: /devops:monitor n8n-mcp
└── Integration Points
    ├── /workflow:create (can use n8n)
    └── /agent:route (n8n automation tasks)
```

### Monitor View

```
MCP SERVERS - REAL-TIME MONITORING
═════════════════════════════════════════════════════════════════

Live Updates (refreshed every 5 seconds)

GITHUB
  Requests (last 60s): ▂▃▃▄▃▅▄▂▂▁ (28 total)
  Response Time: 245ms avg (min: 12ms, max: 1.2s)
  Error Rate: 0% (last 60s)
  Status: ✅ HEALTHY

POSTGRESQL
  Queries (last 60s): ▂▃▂▃▃▂▃▂▂▁ (24 total)
  Avg Query Time: 127ms (min: 5ms, max: 2.1s)
  Connections: 2/10 in use
  Cache Hit: 92%
  Status: ✅ HEALTHY

SLACK
  API Calls (last 60s): ▂▂▂▂▂▂▂▂▁▁ (14 total)
  Response Time: 89ms avg
  Error Rate: 0%
  Status: ✅ HEALTHY

N8N
  Requests (last 60s): ▂▂▂▂▂▂▂▂▂▁ (8 total) ⚠️ Lower than usual
  Response Time: 1.2s avg (elevated)
  Error Rate: 2.4%
  Status: ⚠️ DEGRADED - Investigating...

Press 'q' to exit monitoring | Last updated: 2025-11-25 16:35:42
```

## Command Usage

### Basic List

```bash
/mcp:list
```

Shows quick summary of all servers with basic status.

### Detailed View

```bash
/mcp:list --detailed
```

Shows complete information for each server:

- Full authentication details
- All available operations
- Performance metrics
- Resource usage
- Integration points
- Recent activities

### Filter by Category

```bash
/mcp:list --filter storage
# Shows: Google Drive, AWS S3, Azure Storage

/mcp:list --filter integration
# Shows: n8n, Zapier, Make, etc.

/mcp:list --filter communication
# Shows: Slack, Email, SMS, etc.

/mcp:list --filter data
# Shows: PostgreSQL, MongoDB, Firestore, etc.
```

### Test Connections

```bash
/mcp:list --test-connections
```

Pings all installed MCP servers and reports connectivity status:

```
Testing MCP Server Connections...

GitHub
  ✅ Connection: OK (245ms)
  ✅ Authentication: Valid
  ✅ Permissions: Verified
  ✅ Rate Limits: 60/60 remaining

PostgreSQL
  ✅ Connection: OK (89ms)
  ✅ Authentication: Valid
  ✅ Database Access: Verified
  ✅ Query Performance: Normal

Slack
  ✅ Connection: OK (156ms)
  ✅ Authentication: Valid
  ✅ Bot Permissions: Verified

n8n
  ⚠️  Connection: Timeout (>2s)
  ⚠️  Status: Server may be unavailable
  ❌ Recommendation: Check server status and restart if needed

Summary: 3/4 servers healthy | 1/4 with issues
```

### Real-Time Monitoring

```bash
/mcp:list --monitor
```

Live dashboard showing:

- Active requests per server
- Response times
- Error rates
- Connection status
- Resource usage

Press 'q' to exit or Ctrl+C.

### Format Options

```bash
# Table format (default)
/mcp:list --format table

# JSON format (for automation)
/mcp:list --format json

# Markdown format (for documentation)
/mcp:list --format markdown
```

### JSON Output Example

```json
{
  "timestamp": "2025-11-25T16:35:42Z",
  "servers_installed": 4,
  "servers_connected": 3,
  "servers": {
    "github": {
      "status": "connected",
      "version": "1.2.0",
      "authenticated": true,
      "uptime_percent": 99.8,
      "operations": 47,
      "last_activity": "2025-11-25T16:35:00Z",
      "metrics": {
        "avg_response_time_ms": 245,
        "error_rate": 0.01,
        "requests_today": 247
      }
    },
    "postgres": {
      "status": "connected",
      "version": "1.1.3",
      "authenticated": true,
      "uptime_percent": 100,
      "operations": 12,
      "last_activity": "2025-11-25T16:35:30Z",
      "metrics": {
        "avg_query_time_ms": 127,
        "connections_used": 2,
        "cache_hit_rate": 92
      }
    }
  },
  "available_servers": [
    {
      "name": "stripe",
      "category": "payment-processing",
      "auth_type": "api-key",
      "installation_command": "/mcp:install stripe"
    }
  ]
}
```

## Integration Examples

### Check Before Running Agent Task

```bash
# Verify MCP servers needed for task are available
/mcp:list --test-connections

# If all green, proceed with task
/agent:route "Search GitHub issues and create Slack alert if critical found"
```

### Monitor During Workflow Execution

```bash
# Start monitoring in background
/mcp:list --monitor &

# Run workflow that uses multiple MCP servers
/workflow:create --uses github,postgres,slack,n8n
```

### Auto-Scaling Based on Server Health

```bash
# Check server health before critical operations
/mcp:list --detailed --filter data

# If PostgreSQL response time elevated, defer sync
if [[ $(mcp:list --format json | jq '.servers.postgres.metrics.avg_query_time_ms') -gt 500 ]]; then
  echo "PostgreSQL elevated latency - deferring sync"
  /workflow:defer "DataSync" --delay 30m
fi
```

### Documentation Generation

```bash
# Generate markdown documentation of all available MCP integrations
/mcp:list --format markdown > MCP_CAPABILITIES.md

# Commit to repository
git add MCP_CAPABILITIES.md
git commit -m "docs: Update MCP server capabilities"
```

## Dashboard View

For terminal-based dashboard access:

```bash
/ui:dashboard --mcp-focus
```

This opens the web dashboard with MCP-specific metrics:

- Server status (real-time)
- Operation success rates
- Performance trends
- Quota usage
- Error patterns
- Cost analysis

## Troubleshooting

### Server Shows "Not Connected"

```bash
# Test connection
/mcp:list --test-connections

# Check logs
tail -f ~/.mcp/logs/github.log

# Verify credentials
/mcp:configure github --test-auth

# Reconnect
/mcp:configure github --force-reconnect
```

### "Degraded" Status

```bash
# View detailed diagnostics
/mcp:list --detailed --filter n8n

# Check server health
/devops:monitor n8n-mcp --metrics latency,errors

# View recent errors
grep ERROR ~/.mcp/logs/n8n.log | tail -20
```

### Quota Limits Reached

```bash
# Check current usage
/mcp:list --detailed

# Wait for quota reset
# Or upgrade API plan in server settings
/mcp:configure github --view-rate-limits

# Implement request caching
/mcp:configure github --enable-caching
```

## Advanced Options

### Export Server Configuration

```bash
# Export for backup/sharing (without credentials)
/mcp:list --export-config ~/mcp-servers-config.json

# Useful for team onboarding
```

### Compare Server Capabilities

```bash
# Compare multiple servers
/mcp:list --compare github,gitlab,bitbucket

# Shows: feature matrix, pricing, latency, compatibility
```

### Show Unused Servers

```bash
# Identify servers with no activity
/mcp:list --show-unused --days 7

# Helps clean up unused integrations
```

## Integration with Other Commands

```bash
# Use MCP list data in scripts
mcp_servers=$(mcp:list --format json)

# Check if specific server available
if grep -q '"status": "connected"' <<< $(mcp:list --format json | jq '.servers.github'); then
  echo "GitHub MCP available - proceeding"
  /dev:create-pr --using-github-mcp
fi

# Monitor during deployment
/mcp:list --monitor &
/devops:deploy production --using-mcp-servers
```

## Environment Variables

```bash
# Adjust monitoring refresh rate (ms)
export MCP_MONITOR_INTERVAL=5000

# Show extended metrics
export MCP_METRICS_EXTENDED=true

# Filter servers in list output
export MCP_LIST_FILTER=connected

# Output format
export MCP_OUTPUT_FORMAT=json
```

## Related Commands

- `/mcp:install` - Install new MCP servers
- `/mcp:configure` - Configure server connections
- `/mcp:marketplace` - Browse and install from MCP marketplace
- `/devops:monitor` - Real-time monitoring dashboard
- `/ui:dashboard` - Web-based MCP management interface
- `/agent:route` - Route tasks using available MCP servers
