---
description: Install MCP servers (GitHub, n8n, postgres, custom) to unlock ecosystem integrations
argument-hint: <server-name> [--custom-url <url>] [--auth-type <oauth|api-key|none>] [--verify]
model: claude-3-5-haiku-20241022
allowed-tools:
  - Bash
  - Write
  - Read
  - Grep
---

# MCP Server Installation Command

## Overview

Install Model Context Protocol (MCP) servers to unlock integrations with external services, data sources, and automation platforms. MCP servers act as bridges between Claude and third-party systems, enabling AI agents to directly access and manipulate external resources.

## Supported MCP Servers

### Production-Ready Servers

| Server | Use Case | Authentication | Status |
|--------|----------|-----------------|--------|
| **GitHub** | Repository management, issue tracking, PR operations | OAuth / Personal Token | ✅ Ready |
| **PostgreSQL** | Database queries, schema management, data operations | User/Password + SSL | ✅ Ready |
| **Google Drive** | Document management, file operations, collaboration | OAuth 2.0 | ✅ Ready |
| **Slack** | Team messaging, notifications, workflow automation | Bot Token | ✅ Ready |
| **n8n** | Workflow automation, task orchestration, integrations | API Key | ✅ Ready |
| **Stripe** | Payment processing, subscription management, billing | API Key | ✅ Ready |
| **Notion** | Database management, documentation, content creation | API Token | ✅ Ready |
| **Linear** | Issue tracking, project management, team collaboration | API Key | ✅ Ready |

### In Development

- Zoho CRM (native integration)
- Zoho Mail (native integration)
- Zoho SMS (native integration)
- Salesforce
- AWS S3
- Azure Storage
- MongoDB

## Installation Steps

### Step 1: Verify Requirements

Check that your system has the required dependencies:

- Node.js 16+ (for npm-based MCP servers)
- Python 3.8+ (for Python-based MCP servers)
- `mcp-client` CLI installed (or will be installed)

### Step 2: Select Server

Choose from the supported servers above or provide a custom server URL.

**Built-in servers** (npm/pip based):

- `github`
- `postgres`
- `google-drive`
- `slack`
- `n8n`
- `stripe`
- `notion`
- `linear`

**Custom servers**:

```bash
mcp:install --custom-url https://github.com/user/custom-mcp-server.git
```

### Step 3: Authentication Configuration

Different servers require different authentication methods:

**OAuth-based** (GitHub, Google Drive, Slack):

- Requires browser-based login
- Automatically opens authentication flow
- Stores tokens in `.mcp/auth/` (encrypted)

**API Key-based** (n8n, Stripe, Notion, Linear):

- Requires API key/token
- Prompted interactively
- Stored securely in environment file

**Connection String-based** (PostgreSQL):

- Requires user, password, host, port, database
- Prompted interactively
- Can include SSL options

**No Auth** (Local services):

- Direct connection without credentials
- Example: Local PostgreSQL instance

### Step 4: Verification

After installation, the system will:

1. Verify credentials/authentication
2. Test basic connectivity
3. List available operations
4. Display integration examples

## Usage Examples

### Example 1: Install GitHub MCP Server

```bash
/mcp:install github
```

**Interactive Flow**:

```
Installing GitHub MCP Server...

Checking dependencies... ✓ Node.js 18.0.0 found
Downloading server... ✓ github-mcp@1.2.0

Authentication Setup:
  [ Opens browser for GitHub OAuth login ]

  ✓ Authentication successful
  ✓ Linked to account: @username
  ✓ Scopes granted: repo, read:user, read:org

Verifying connection... ✓
Testing permissions... ✓ Can access 42 repositories

Installation Complete!
Location: ~/.mcp/servers/github
Config: ~/.mcp/config/github.json

Available Operations:
  - Get repository info (async)
  - List repositories
  - Create GitHub issues
  - Create pull requests
  - Comment on issues/PRs
  - Manage repository labels
  - Create releases
  - Update branch protection rules

Next Steps:
  1. View configuration: /mcp:configure github
  2. Test in agent: /agent:route "Create a GitHub issue"
  3. Integrate with workflow: See /mcp:list for integration examples
```

### Example 2: Install PostgreSQL MCP Server

```bash
/mcp:install postgres
```

**Interactive Flow**:

```
Installing PostgreSQL MCP Server...

Checking dependencies... ✓ Python 3.9.0 found

Connection Details Required:
  Host [localhost]: mydb.example.com
  Port [5432]: 5432
  Username: analytics_user
  Password: ••••••••••••••
  Database: production_db
  SSL Mode [disable]: require

Verifying connection... ✓
Connected to PostgreSQL 13.8

Database Info:
  Tables: 47
  Functions: 12
  Views: 8

Installation Complete!
Location: ~/.mcp/servers/postgres
Config: ~/.mcp/config/postgres.json (encrypted)

Available Operations:
  - Execute SELECT queries
  - Get table schema
  - Get column statistics
  - Execute prepared statements
  - List tables and views
  - Describe table structure

Security Notes:
  - Password stored in encrypted vault
  - Connection uses SSL/TLS
  - Query logging available at ~/.mcp/logs/postgres.log

Next Steps:
  1. Configure advanced settings: /mcp:configure postgres
  2. Test queries: /db:query "natural language query"
  3. Set up monitoring: /devops:monitor postgres-mcp
```

### Example 3: Install n8n MCP Server

```bash
/mcp:install n8n --custom-url https://n8n.example.com
```

**Interactive Flow**:

```
Installing n8n MCP Server...

Checking dependencies... ✓ Node.js 18.0.0 found

Server Configuration:
  Server URL: https://n8n.example.com
  API Key: ••••••••••••••••••••••••••••••••

Verifying connection... ✓
Connected to n8n v1.15.0

Available Workflows: 23
  - Customer Onboarding
  - Email Campaign Dispatcher
  - Data Sync: Salesforce → Analytics
  - Invoice Generator
  - Slack Notifications

Installation Complete!
Location: ~/.mcp/servers/n8n
Config: ~/.mcp/config/n8n.json (encrypted)

Available Operations:
  - List workflows
  - Trigger workflow execution
  - Get execution history
  - Create workflow
  - Update workflow
  - Delete workflow
  - Monitor workflow status

Integration Examples:
  /agent:route "Trigger n8n customer onboarding workflow for new CRM leads"
  /workflow:create --platform n8n --name "Auto-sync"

Next Steps:
  1. List available workflows: /mcp:list --detailed
  2. Create automation: /workflow:create --uses n8n
  3. Monitor executions: /devops:monitor n8n-mcp
```

### Example 4: Install Custom MCP Server

```bash
/mcp:install --custom-url https://github.com/myorg/custom-mcp-server.git --auth-type api-key
```

**Interactive Flow**:

```
Installing Custom MCP Server...

Cloning repository... ✓
Installing dependencies... ✓
Building project... ✓

API Key Setup:
  Provide your API key for the custom server:
  API Key: ••••••••••••••••••••••••••••••••

Verifying connection... ✓
Server online and responding

Available Operations: 12
  - Operation 1
  - Operation 2
  - ...

Installation Complete!
Location: ~/.mcp/servers/custom
Config: ~/.mcp/config/custom.json (encrypted)
```

## Integration with Existing Commands

### With /agent Commands

```bash
# Route task to appropriate agent with MCP context
/agent:route "Search GitHub issues for security vulnerabilities"
# Automatically uses GitHub MCP if installed

/agent:route "Query production database for customer metrics"
# Automatically uses PostgreSQL MCP if installed
```

### With /workflow Commands

```bash
# Create workflow using installed MCP servers
/workflow:create --name "Sync CRM to n8n" --uses n8n,github
# Uses both n8n and GitHub MCP servers

/workflow:create --name "Auto-file-uploads" --uses google-drive
# Creates workflow using Google Drive MCP
```

### With /zoho Commands

```bash
# Zoho operations enhanced by MCP servers
/zoho:sync-data --source postgres-mcp --target zoho-crm
# Sync database records to Zoho CRM

/zoho:create-lead --use-data-from github-mcp
# Create CRM lead from GitHub repository data
```

### With /dev Commands

```bash
# Development operations using GitHub MCP
/dev:create-pr --repository "from github-mcp" --base main
# Create pull request using GitHub MCP

/dev:contract-test --spec "from github-mcp" --mode validate
# Validate API contract using GitHub repository spec
```

## Security Considerations

### Credential Management

- All credentials stored in `~/.mcp/auth/` with encryption
- API keys stored in encrypted environment files
- Tokens refreshed automatically
- No credentials in command history or logs

### Network Security

- All connections use TLS/SSL where available
- Support for corporate proxies
- VPN-compatible server connections
- Audit logging of all operations

### Rate Limiting & Quotas

- Automatic rate limit detection
- Backoff strategies for quota management
- Per-server quota monitoring
- `/mcp:list --monitor` for quota dashboard

### Access Control

- Per-server permission scopes (OAuth)
- API key rotation capabilities
- Revocation of individual server credentials
- Audit trail of all MCP operations

### Best Practices

1. **Use OAuth over API Keys when possible**
   - Reduces attack surface
   - Easier credential rotation
   - Automatic token refresh

2. **Limit Server Permissions**
   - Only grant required OAuth scopes
   - Use read-only API keys for queries
   - Use separate keys for different environments

3. **Rotate Credentials Regularly**

   ```bash
   /mcp:configure github --rotate-credentials
   /mcp:configure postgres --rotate-password
   ```

4. **Monitor MCP Activity**

   ```bash
   /mcp:list --monitor
   /devops:monitor mcp --metrics requests,errors,latency
   ```

5. **Secure Configuration Files**
   - Encrypt `.mcp/config/` directory
   - Exclude from version control
   - Restrict file permissions to owner only

## Troubleshooting

### Installation Fails

**Problem**: "Dependency not found"

```bash
# Solution: Install dependencies
npm install -g mcp
pip install mcp-client
```

**Problem**: "Authentication failed"

```bash
# Solution: Verify credentials
/mcp:configure github --test-auth
# Or re-authenticate
/mcp:install github --force-reauth
```

### Connection Issues

**Problem**: "Cannot reach server"

```bash
# Solution: Check connectivity
/mcp:list --test-connections
# View logs
tail -f ~/.mcp/logs/all.log
```

**Problem**: "Rate limit exceeded"

```bash
# Solution: Check quotas
/mcp:list --monitor
# Wait for reset or upgrade API plan
```

### Removing Servers

```bash
# Uninstall specific server
rm -rf ~/.mcp/servers/github
rm ~/.mcp/config/github.json

# Or use management command (when available)
/mcp:list --uninstall github
```

## Advanced Options

### Offline Installation

```bash
/mcp:install github --offline --cache-path /path/to/cache
```

### Docker-based MCP Servers

```bash
/mcp:install postgres --docker --image postgres:15-alpine
```

### Custom Port Configuration

```bash
/mcp:install --custom-url http://localhost:9000 --port 9000
```

### Proxy Configuration

```bash
/mcp:install github --proxy https://proxy.company.com:8080 --proxy-auth user:pass
```

## Next Steps

After installation:

1. **Verify Installation**

   ```bash
   /mcp:list
   # Shows all installed servers
   ```

2. **Configure as Needed**

   ```bash
   /mcp:configure github --set-default-repo myorg/myrepo
   /mcp:configure postgres --set-timeout 30s
   ```

3. **Create Workflows**

   ```bash
   /workflow:create --name "Auto-PR-Reviews" --uses github-mcp
   /workflow:create --name "Data-Sync" --uses postgres-mcp,zoho-crm
   ```

4. **Monitor Usage**

   ```bash
   /mcp:list --monitor
   /devops:monitor mcp-servers --metrics requests,errors
   ```

5. **Integrate with Agents**

   ```bash
   /agent:route "Use installed MCP servers to complete task X"
   ```

## Supported Platforms

- macOS (Intel & Apple Silicon)
- Linux (Ubuntu, Debian, CentOS, Alpine)
- Windows (WSL2 recommended)
- Docker containers
- Cloud Functions (GCP, AWS Lambda, Azure Functions)

## Environment Variables

```bash
# Set default MCP data directory
export MCP_HOME=~/.mcp

# Enable debug logging
export MCP_DEBUG=true

# Set proxy for all servers
export MCP_PROXY=https://proxy.company.com:8080

# Disable telemetry
export MCP_TELEMETRY=disabled
```

## Documentation References

- [MCP Protocol Specification](https://modelcontextprotocol.io)
- [Available MCP Servers](https://modelcontextprotocol.io/servers)
- [MCP Client Implementation](https://github.com/modelcontextprotocol/python-sdk)
- Project: `/guides/` for integration patterns
