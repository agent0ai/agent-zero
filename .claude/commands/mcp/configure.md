---
description: Configure MCP server connections, credentials, permissions, rate limits, and advanced settings
argument-hint: <server-name> [--set-<option> <value>] [--test-auth] [--rotate-credentials] [--view-config] [--reset]
model: claude-3-5-haiku-20241022
allowed-tools:
  - Read
  - Write
  - Bash
---

# MCP Server Configuration Command

## Overview

Manage advanced configuration for installed Model Context Protocol servers. Configure authentication, set defaults, manage permissions, adjust rate limits, enable caching, and troubleshoot connection issues.

## Server-Specific Configuration

### GitHub MCP Configuration

```bash
/mcp:configure github --view-config
```

**Available Options**:

```
Authentication & Access
  --set-auth-type <oauth|personal-token>
  --set-username <username>
  --test-auth                          # Verify credentials are valid
  --rotate-credentials                 # Generate new token

Defaults & Scoping
  --set-default-repo <owner/repo>     # Default repository for operations
  --set-default-org <organization>    # Default organization
  --set-api-version <v3|v4>           # API version preference

Permissions & Scoping
  --set-scopes <comma-separated>      # Update OAuth scopes
  --view-permissions                   # Show current permissions
  --request-additional-scopes          # Request new scopes

Performance Tuning
  --set-timeout <seconds>              # Request timeout (default: 30)
  --set-max-retries <number>          # Retry count (default: 3)
  --enable-caching                     # Cache API responses
  --set-cache-ttl <seconds>           # Cache duration (default: 3600)
  --enable-batch-requests             # Combine multiple requests

Rate Limiting
  --view-rate-limits                   # Show current quotas
  --set-rate-limit <requests/hour>    # Custom rate limit
  --enable-backoff                     # Auto-backoff on rate limits

Logging & Monitoring
  --set-log-level <debug|info|warn|error>
  --enable-request-logging            # Log all API requests
  --view-recent-errors [--limit 10]   # Show error history
```

**Example Configurations**:

```bash
# Set default repository for all GitHub operations
/mcp:configure github --set-default-repo myorg/myrepo

# Verify authentication works
/mcp:configure github --test-auth
# Output:
# ✅ Authentication verified
# Account: @username
# Scopes: repo, read:user, read:org
# Rate Limit: 60/60 requests remaining
# Last used: 2025-11-25 16:30:00

# Update OAuth scopes to include gist management
/mcp:configure github --set-scopes repo,read:user,gist

# Enable caching for read operations
/mcp:configure github --enable-caching --set-cache-ttl 1800

# Set aggressive retry for reliability
/mcp:configure github --set-max-retries 5 --set-timeout 60

# View current configuration
/mcp:configure github --view-config
# Output shows:
# Default Repository: myorg/myrepo
# Authentication: OAuth (valid)
# Caching: Enabled (30 min TTL)
# Timeout: 60s
# Max Retries: 5
# Rate Limit: 60 requests/hour
```

### PostgreSQL MCP Configuration

```bash
/mcp:configure postgres --view-config
```

**Available Options**:

```
Connection Settings
  --set-host <hostname>               # Database host
  --set-port <port>                   # Database port (default: 5432)
  --set-username <user>               # Database user
  --set-password <password>           # Database password (prompted)
  --set-database <dbname>             # Default database

Security & Encryption
  --set-ssl-mode <disable|allow|prefer|require|require-verify-ca|require-verify-full>
  --set-ca-cert <path>                # CA certificate path
  --set-client-cert <path>            # Client certificate path
  --set-client-key <path>             # Client key path
  --test-auth                         # Test connection with current credentials
  --rotate-password                   # Generate and set new password

Query Execution
  --set-query-timeout <seconds>       # Query timeout (default: 30)
  --set-statement-timeout <seconds>   # PostgreSQL statement timeout
  --set-idle-in-transaction-timeout <seconds>
  --set-max-connections <number>      # Max concurrent connections
  --enable-connection-pooling         # Use pgBouncer or similar
  --set-pool-size <number>            # Connection pool size

Performance Tuning
  --enable-query-caching              # Cache query results
  --set-cache-ttl <seconds>          # Cache TTL (default: 300)
  --enable-batch-queries              # Batch multiple queries
  --enable-prepared-statements        # Use prepared statements
  --set-plan-cache-size <number>      # Query plan cache size

Data & Schema
  --set-search-path <schemas>         # Search path for tables
  --enable-read-only                  # Read-only connection mode
  --set-default-schema <schema>       # Default schema

Logging & Monitoring
  --enable-query-logging              # Log all executed queries
  --set-log-level <debug|info|warn|error>
  --view-table-stats [--table name]   # Show table statistics
  --view-slow-queries [--threshold 1000]  # Show queries >1s
```

**Example Configurations**:

```bash
# Update connection settings
/mcp:configure postgres \
  --set-host analytics.company.com \
  --set-database reporting \
  --set-ssl-mode require

# Test new connection
/mcp:configure postgres --test-auth
# Output:
# ✅ Connection successful
# Server: PostgreSQL 13.8
# Connected to: analytics.company.com:5432/reporting
# User: analytics_user
# SSL: Enabled (verify-full)

# Enable connection pooling
/mcp:configure postgres \
  --enable-connection-pooling \
  --set-pool-size 10 \
  --set-query-timeout 60

# Enable performance optimization
/mcp:configure postgres \
  --enable-query-caching \
  --set-cache-ttl 600 \
  --enable-prepared-statements

# Monitor table statistics
/mcp:configure postgres --view-table-stats
# Output:
# Table Statistics
# ─────────────────────────────────────
# customers (rows: 1.2M, size: 847MB)
# orders (rows: 4.8M, size: 2.3GB)
# products (rows: 15K, size: 42MB)
# ...

# Find slow queries
/mcp:configure postgres --view-slow-queries --threshold 500
# Output:
# Queries taking >500ms (last 24 hours)
# ──────────────────────────────────────
# 1. SELECT ... FROM orders JOIN customers ... (avg: 2.4s, count: 23)
# 2. SELECT ... FROM analytics WHERE date > ... (avg: 1.2s, count: 156)
```

### Slack MCP Configuration

```bash
/mcp:configure slack --view-config
```

**Available Options**:

```
Workspace & Authentication
  --set-workspace <name>              # Set default workspace
  --set-bot-token <token>             # Update bot token
  --set-user-token <token>            # Update user token
  --test-auth                         # Verify tokens are valid
  --rotate-credentials                # Refresh tokens

Default Channels & Users
  --set-default-channel <#channel>    # Default channel for messages
  --set-default-user <@user>          # Default recipient user

Message Formatting
  --set-message-format <plain|markdown|blocks>
  --set-emoji-style <native|codes>
  --enable-mentions                   # Allow @mentions in messages
  --enable-formatting                 # Allow bold, italic, code, etc.

Permissions & Scope
  --view-permissions                  # Show bot scopes
  --request-permissions <scopes>      # Request additional scopes

Rate Limiting & Performance
  --view-rate-limits                  # Show API quotas
  --set-batch-size <number>          # Message batch size
  --enable-request-caching           # Cache API responses
  --set-timeout <seconds>            # Request timeout

Threading & Context
  --enable-threaded-replies          # Use message threads
  --set-conversation-depth <number>  # Max conversation depth
  --enable-message-updates           # Update previous messages

Logging & Monitoring
  --set-log-level <debug|info|warn|error>
  --enable-interaction-logging       # Log user interactions
  --view-message-history [--limit 100]  # Show recent messages
```

**Example Configurations**:

```bash
# Set default channel for alerts
/mcp:configure slack \
  --set-default-channel "#alerts" \
  --set-message-format markdown

# Enable threaded replies for conversations
/mcp:configure slack \
  --enable-threaded-replies \
  --set-conversation-depth 10

# Test authentication
/mcp:configure slack --test-auth
# Output:
# ✅ Authentication verified
# Workspace: example-workspace
# Bot User: @claude-ai
# Scopes: chat:write, channels:read, users:read, [12 more]
# Rate Limit: 30 requests/minute

# View recent message history
/mcp:configure slack --view-message-history --limit 20
```

### n8n MCP Configuration

```bash
/mcp:configure n8n --view-config
```

**Available Options**:

```
Server & Authentication
  --set-server-url <url>              # n8n instance URL
  --set-api-key <key>                 # Update API key
  --test-auth                         # Verify API key is valid
  --rotate-credentials                # Generate new API key

Default Workflow Settings
  --set-default-workflow <id|name>    # Default workflow for triggers
  --set-execution-mode <background|foreground>
  --set-execution-timeout <seconds>   # Max execution time

Webhook & Trigger Configuration
  --set-webhook-base-url <url>        # Webhook URL base
  --enable-webhook-auth               # Require webhook authentication
  --set-webhook-secret <secret>       # Webhook secret token

Performance Tuning
  --set-max-concurrent-executions <number>
  --enable-workflow-caching           # Cache workflow definitions
  --set-cache-ttl <seconds>
  --enable-batch-operations           # Batch multiple operations
  --set-timeout <seconds>

Logging & Monitoring
  --set-log-level <debug|info|warn|error>
  --enable-execution-logging          # Log all executions
  --view-workflow-stats               # Show workflow performance
  --view-recent-errors [--limit 20]   # Show error history
```

**Example Configurations**:

```bash
# Configure webhooks for incoming triggers
/mcp:configure n8n \
  --set-webhook-base-url "https://n8n.company.com/webhook" \
  --enable-webhook-auth

# Set execution limits
/mcp:configure n8n \
  --set-max-concurrent-executions 10 \
  --set-execution-timeout 300

# Test connection
/mcp:configure n8n --test-auth
# Output:
# ✅ Connection successful
# Server: n8n v1.15.0
# URL: https://n8n.company.com
# API Key: Valid
# Available Workflows: 23

# Monitor workflow performance
/mcp:configure n8n --view-workflow-stats
# Output:
# Workflow Performance (last 7 days)
# ────────────────────────────────────
# Customer Onboarding
#   Executions: 156 | Success: 154 (98.7%) | Avg: 2.3s
# Email Campaign
#   Executions: 45 | Success: 45 (100%) | Avg: 1.8s
# Data Sync: Salesforce
#   Executions: 84 | Success: 82 (97.6%) | Avg: 45s
```

## Global Configuration Options (All Servers)

```bash
# Display full configuration
/mcp:configure <server-name> --view-config

# Reset to defaults
/mcp:configure <server-name> --reset

# Export configuration (without credentials)
/mcp:configure <server-name> --export-config ~/backup.json

# Import configuration
/mcp:configure <server-name> --import-config ~/backup.json

# Validate configuration
/mcp:configure <server-name> --validate

# Rotate all credentials
/mcp:configure <server-name> --rotate-all-credentials
```

## Interactive Configuration

For interactive setup wizard:

```bash
/mcp:configure github --interactive
```

This launches an interactive questionnaire:

```
GitHub MCP Configuration Wizard
════════════════════════════════════════

1. Authentication Method
   a) OAuth (recommended, browser-based)
   b) Personal Access Token (manual)

   Select [a/b]: a

   ✓ Opening GitHub OAuth login in browser...
   ✓ Waiting for authorization...
   ✓ Authorization successful!

2. Default Repository
   Which repository should be the default for operations?

   Repositories found: 42
   1) prompt-blueprint (Owner)
   2) ai-agents (Contributor)
   3) data-science-toolkit (Contributor)
   ...

   Select [1-42]: 1
   ✓ Set default repository to: myorg/prompt-blueprint

3. Feature Configuration
   ✓ Enable caching? [y/n]: y
   ✓ Cache TTL (seconds) [3600]:
   ✓ Enable request logging? [y/n]: n
   ✓ Set API timeout (seconds) [30]: 60

4. Review Configuration
   Default Repository: myorg/prompt-blueprint
   Authentication: OAuth
   Caching: Enabled (1 hour TTL)
   API Timeout: 60s

   ✓ Configuration saved successfully!
```

## Viewing Configuration

### View Configuration File

```bash
/mcp:configure github --view-config
```

Output (with credentials masked):

```yaml
server: github
version: 1.2.0
authentication:
  type: oauth
  username: myusername
  scopes:
    - repo
    - read:user
    - read:org
  token: ••••••••••••••••••••••••••••••••••••••••• (masked)
  token_expires: 2025-12-25T14:30:00Z

defaults:
  repository: myorg/prompt-blueprint
  organization: myorg
  api_version: v3

performance:
  timeout: 30
  max_retries: 3
  caching: enabled
  cache_ttl: 3600
  batch_requests: enabled

logging:
  level: info
  request_logging: false

created: 2025-11-15T10:00:00Z
last_updated: 2025-11-25T16:30:00Z
```

## Rotating Credentials

### Automatic Credential Rotation

```bash
/mcp:configure github --rotate-credentials
```

Process:

1. Generate new token in service (GitHub, n8n, etc.)
2. Test new token
3. Update local configuration
4. Verify old token revocation

```
Rotating GitHub credentials...

✓ Generating new personal access token
✓ Testing new token authentication
✓ Updating local configuration
✓ Verifying connection with new token
✓ Revoking old token

Rotation complete!
New token expires: 2025-12-25T16:30:00Z
```

### Manual Credential Update

```bash
/mcp:configure github --set-username newusername
/mcp:configure postgres --set-password
# (will prompt for password securely)
```

## Troubleshooting Configuration Issues

### Test Authentication

```bash
/mcp:configure postgres --test-auth
```

Detailed output:

```
Testing PostgreSQL connection...

Attempting connection to postgres.example.com:5432...
✓ Network connection: OK (89ms)
✓ Authentication: Valid (user: analytics_user)
✓ Database access: confirmed (databases: 8)
✓ Query execution: OK (test query: 45ms)
✓ SSL/TLS: Enabled (verify-full)

Summary: All tests passed ✅
Connection is healthy and ready for operations.
```

### View Configuration Issues

```bash
/mcp:configure n8n --validate
```

Output:

```
Validating n8n configuration...

ℹ Server URL: https://n8n.example.com
✓ URL format: valid
✓ Server reachability: OK (245ms)
✓ API key format: valid
✓ API key authentication: Valid
⚠ Warning: API key expires in 30 days (2025-12-25)

Configuration is valid and healthy.
Action recommended: Rotate API key before expiration
```

## Advanced Customization

### Custom Integration Settings

```bash
# Store custom application-specific settings
/mcp:configure github --set-custom-option app-name "my-app"
/mcp:configure github --set-custom-option branch-prefix "feature/"

# Retrieve custom settings
/mcp:configure github --view-custom-options
```

### Environment-Specific Configuration

```bash
# Load configuration for specific environment
/mcp:configure postgres --load-env production
# Uses ~/.mcp/config/postgres.production.json

/mcp:configure postgres --load-env staging
# Uses ~/.mcp/config/postgres.staging.json
```

## Integration with Other Commands

```bash
# Configure before using in workflows
/mcp:configure github --set-default-repo myorg/repo
/workflow:create --uses github-mcp

# Verify configuration before critical operations
/mcp:configure postgres --test-auth
/db:query "SELECT * FROM sensitive_table"

# Use configured defaults in agents
/agent:route "Create PR in configured repository"
# Uses --set-default-repo setting
```

## Related Commands

- `/mcp:install` - Install new MCP servers
- `/mcp:list` - View server status and capabilities
- `/mcp:marketplace` - Browse MCP marketplace
- `/devops:monitor` - Monitor server performance
