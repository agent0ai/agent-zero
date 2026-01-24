---
description: Browse, discover, and install MCP servers from official marketplace with ratings, reviews, and compatibility checking
argument-hint: [--search <query>] [--category <category>] [--sort <downloads|rating|recent>] [--limit <20>] [--install <server-name>] [--details <server-name>]
model: claude-3-5-haiku-20241022
allowed-tools:
  - Bash
  - Read
  - Grep
---

# MCP Marketplace Command

## Overview

Browse the official Model Context Protocol marketplace to discover, review, and install MCP servers. Features advanced filtering, ratings, compatibility checks, installation guidance, and community reviews.

## Default Marketplace View

```bash
/mcp:marketplace
```

Output:

```
MCP MARKETPLACE - Featured Servers
═══════════════════════════════════════════════════════════════════════

Your System: Linux | Node.js 18.0 | Python 3.9 | Docker Available

TOP RATED SERVERS (★ rating)
────────────────────────────────────────────────────────────────────────

1. GitHub MCP                                        ★★★★★ (2,847 reviews)
   By: Anthropic | v1.2.0 | 18,293 downloads | Free
   Repository management, PR operations, issue tracking
   Permissions: OAuth, Personal Token
   Compatibility: ✅ All Platforms
   Install: /mcp:marketplace --install github

2. PostgreSQL MCP                                    ★★★★★ (1,456 reviews)
   By: Open Source Community | v1.1.3 | 8,947 downloads | Free
   Database queries, schema management, analytics
   Permissions: User/Password, SSL/TLS
   Compatibility: ✅ All Platforms
   Install: /mcp:marketplace --install postgres

3. Google Drive MCP                                  ★★★★★ (1,923 reviews)
   By: Google | v2.0.0 | 12,847 downloads | Free
   Document management, file operations, sharing
   Permissions: OAuth 2.0
   Compatibility: ✅ All Platforms
   Install: /mcp:marketplace --install google-drive

4. Slack MCP                                         ★★★★☆ (1,245 reviews)
   By: Slack | v1.0.2 | 6,847 downloads | Free
   Messaging, notifications, workflow automation
   Permissions: Bot Token, User Token
   Compatibility: ✅ All Platforms
   Install: /mcp:marketplace --install slack

5. n8n Workflow MCP                                  ★★★★★ (892 reviews)
   By: n8n | v1.15.0 | 4,567 downloads | Free (requires n8n)
   Workflow automation, task orchestration, integrations
   Permissions: API Key
   Compatibility: ✅ All Platforms
   Install: /mcp:marketplace --install n8n


TRENDING SERVERS (Last 30 days ↑)
────────────────────────────────────────────────────────────────────────

6. Cursor AI Editor MCP                             ★★★★★ (new!)
   By: Anysphere | v0.5.0 | 1,247 downloads | Free
   IDE integration, code navigation, editor automation
   Permissions: API Key
   Compatibility: ✅ Linux, macOS, Windows
   Install: /mcp:marketplace --install cursor-ai

7. TypeScript Type Checker                          ★★★★☆ (↑ +342%)
   By: Microsoft | v5.3.0 | 2,847 downloads | Free
   Static type analysis, TypeScript integration
   Permissions: None (local)
   Compatibility: ✅ All Platforms (requires TypeScript)
   Install: /mcp:marketplace --install typescript-checker

8. Anthropic Docs Browser                           ★★★★★ (↑ +128%)
   By: Anthropic | v2.1.0 | 3,456 downloads | Free
   Access official documentation, API references
   Permissions: None (public content)
   Compatibility: ✅ All Platforms
   Install: /mcp:marketplace --install anthropic-docs


Show more | Next page | Filter | Search
```

## Search & Filter

### Search by Name or Keyword

```bash
/mcp:marketplace --search "database"
```

Output:

```
Search Results for "database" (12 servers found)

1. PostgreSQL MCP                                    ★★★★★ (1,456 reviews)
   Full-featured PostgreSQL integration with query building

2. MongoDB MCP                                       ★★★★☆ (847 reviews)
   NoSQL database management and aggregation

3. Firebase MCP                                      ★★★★☆ (623 reviews)
   Real-time database and authentication

4. Supabase MCP                                      ★★★★★ (512 reviews)
   PostgreSQL with built-in authentication and storage

5. MySQL MCP                                        ★★★★☆ (456 reviews)
   MySQL database queries and schema management

[showing 1-5 of 12, page 1/3]
```

### Filter by Category

```bash
/mcp:marketplace --category communication
```

Available Categories:

- **data**: Database, data warehousing, analytics
- **communication**: Email, SMS, chat, messaging
- **integration**: Zapier, Make, n8n, automation
- **storage**: Cloud storage, file management
- **devops**: CI/CD, monitoring, deployment
- **productivity**: Notes, tasks, calendars
- **payment**: Payment processing, billing
- **healthcare**: HIPAA-compliant, medical data
- **real-estate**: Property management, listings
- **ecommerce**: Store management, inventory
- **crm**: Customer relationship management
- **hr**: Human resources, payroll
- **finance**: Accounting, invoicing, banking
- **custom**: User-created custom servers

```bash
/mcp:marketplace --category communication
```

Output:

```
MCP Servers - Communication Category (18 servers)

1. Slack MCP                                         ★★★★☆ (1,245 reviews)
   Real-time messaging, notifications, workflows

2. Email MCP                                         ★★★★★ (2,156 reviews)
   SMTP, IMAP, Gmail, Outlook, cold email sequences

3. Twilio SMS MCP                                    ★★★★★ (1,847 reviews)
   SMS sending, voice calls, WhatsApp messaging

4. Discord MCP                                      ★★★★☆ (923 reviews)
   Discord server management, bot commands

5. Microsoft Teams MCP                              ★★★★☆ (856 reviews)
   Teams messaging, channel management

[showing 1-5 of 18]
```

### Sort Options

```bash
# Most downloaded servers
/mcp:marketplace --sort downloads

# Highest rated
/mcp:marketplace --sort rating

# Recently added/updated
/mcp:marketplace --sort recent

# Most relevant to your query
/mcp:marketplace --search stripe --sort rating
```

## Detailed Server Information

### View Server Details

```bash
/mcp:marketplace --details github
```

Output:

```
GitHub MCP - Detailed Information
═══════════════════════════════════════════════════════════════════════

OVERVIEW
────────────────────────────────────────────────────────────────────────
Name: GitHub MCP
Developer: Anthropic
Version: 1.2.0 (Latest)
License: Apache 2.0
Repository: https://github.com/modelcontextprotocol/servers/tree/main/github
Official Docs: https://github.com/modelcontextprotocol/servers/blob/main/README.md


RATINGS & REVIEWS
────────────────────────────────────────────────────────────────────────
Overall Rating: ★★★★★ (4.9/5.0)
Total Reviews: 2,847
Downloads: 18,293 (all time)
Monthly Active Users: 4,352

Recent Reviews:
  ★★★★★ "Essential for GitHub automation!" - @dev_enthusiast (3 days ago)
  ★★★★★ "Works perfectly with our CI/CD pipeline" - @platform_eng (1 week ago)
  ★★★★☆ "Great but wish it had branch protection rules" - @infra_team (2 weeks ago)


FEATURES & CAPABILITIES
────────────────────────────────────────────────────────────────────────
Repository Operations
  ✓ Get repository information
  ✓ List repositories (personal, organization)
  ✓ Create repositories
  ✓ Delete repositories
  ✓ Update repository settings
  ✓ Get repository statistics

Issue Management
  ✓ Create issues
  ✓ Update issues
  ✓ Close/reopen issues
  ✓ Add labels
  ✓ Add assignees
  ✓ List issues with filtering
  ✓ Search issues

Pull Request Operations
  ✓ Create pull requests
  ✓ Get PR details
  ✓ List pull requests
  ✓ Add review comments
  ✓ Approve/request changes
  ✓ Merge pull requests
  ✓ Update branch protection

Discussions & Collaboration
  ✓ Comment on issues/PRs
  ✓ Create discussions
  ✓ List discussions
  ✓ Manage reactions

Release Management
  ✓ Create releases
  ✓ List releases
  ✓ Update releases
  ✓ Manage assets

User & Organization
  ✓ Get user information
  ✓ List followers
  ✓ Get organization info
  ✓ List organization members

Advanced Features
  ✓ Webhooks
  ✓ GitHub Actions integration
  ✓ Branch protection rules
  ✓ Repository templates


AUTHENTICATION & PERMISSIONS
────────────────────────────────────────────────────────────────────────
Methods:
  1. OAuth (Recommended)
     - Browser-based login
     - User grants permissions
     - Auto token refresh
     - Scope customization

  2. Personal Access Token
     - Manual token generation
     - Fixed scopes
     - Longer expiration

Required Scopes (default):
  ✓ repo            - Full control of repositories
  ✓ read:user       - Read user profile
  ✓ read:org        - Read organization data
  ✓ workflow        - Update GitHub Actions workflows (optional)
  ✓ gist            - Manage gists (optional)

Rate Limits:
  - API: 60 requests/hour (authenticated)
  - Search: 10 requests/minute


SYSTEM REQUIREMENTS
────────────────────────────────────────────────────────────────────────
Runtime: Node.js 16+
Platform:
  ✅ macOS (Intel & Apple Silicon)
  ✅ Linux (Ubuntu, Debian, CentOS)
  ✅ Windows (WSL2)
  ✅ Docker
  ✅ Cloud Functions

Size: 8.4 MB
Dependencies: axios, octokit

Special Requirements:
  - GitHub account (free or paid)
  - Internet connection


INSTALLATION & SETUP
────────────────────────────────────────────────────────────────────────
Installation Time: ~2 minutes
Configuration Time: ~1 minute (OAuth) or ~5 minutes (token)

Quick Install:
  /mcp:marketplace --install github

Step-by-step:
  1. Run installation command
  2. Authenticate with GitHub (OAuth or token)
  3. Verify connection
  4. Set default repository (optional)


COMMON INTEGRATION PATTERNS
────────────────────────────────────────────────────────────────────────

Pattern 1: Automated PR Reviews
  - Use with code review agents
  - Integrate with CI/CD pipelines
  - Auto-assign reviewers
  Example: /agent:route "Review all PRs in myorg/repo"

Pattern 2: Issue Automation
  - Create issues from Slack messages
  - Route GitHub issues to Zoho CRM
  - Auto-close issues with labels
  Example: /zoho:sync-data --source github-mcp --target zoho-crm

Pattern 3: Release Management
  - Automated release notes
  - Create releases from commit history
  - Asset management
  Example: /workflow:create --uses github-mcp --type release

Pattern 4: Dashboard Integration
  - Repository metrics dashboard
  - PR/issue status board
  - Contributor analytics
  Example: /ui:dashboard --source github-mcp


PRICING & LICENSING
────────────────────────────────────────────────────────────────────────
Server Cost: Free
GitHub API Cost: Free (with rate limits)
License: Apache 2.0 (open source)

Limitations:
  - Rate limits apply (60 req/hour for API)
  - GitHub API pricing for large organizations
  - No guaranteed uptime


SUPPORT & RESOURCES
────────────────────────────────────────────────────────────────────────
Documentation: https://github.com/modelcontextprotocol/servers/blob/main/README.md
Issues & Bugs: https://github.com/modelcontextprotocol/servers/issues
Community: GitHub Discussions, Discord
Response Time: < 24 hours for critical issues


COMPATIBILITY CHECKLIST
────────────────────────────────────────────────────────────────────────
✅ Compatible with Claude 3.5 Sonnet
✅ Compatible with Claude 3 Opus
✅ Works with all Prompt Blueprint agents
✅ Integrates with /dev commands
✅ Integrates with /workflow commands
✅ Integrates with /agent:route
✅ Can sync data to Zoho CRM
✅ Works offline (cached operations)
✅ Supports batch operations
✅ API rate-limiting handled

⚠️  Notes:
   - Some features require GitHub Pro or Enterprise
   - Branch protection rules need admin access
   - GitHub Actions workflows need elevated permissions


VERSION HISTORY
────────────────────────────────────────────────────────────────────────
v1.2.0 (Current) - Nov 2024
  + Added branch protection rules
  + Added GitHub Actions workflows
  + Improved error handling
  ✓ 99.8% uptime

v1.1.0 - Oct 2024
  + Added webhooks support
  + Performance improvements

v1.0.0 - Sep 2024
  ✓ Initial release


RELATED SERVERS
────────────────────────────────────────────────────────────────────────
Often installed together with:
  • GitLab MCP (for GitLab repositories)
  • GitHub Actions MCP (for workflow automation)
  • Slack MCP (for notifications)
  • n8n MCP (for automation workflows)


ACTION
────────────────────────────────────────────────────────────────────────
Install: /mcp:marketplace --install github
Reviews: Show more user reviews
Discussion: Join community discussions
Feedback: Report issues or suggest features
```

## Installation from Marketplace

### One-Click Installation

```bash
/mcp:marketplace --install github
```

Installation process:

```
Installing GitHub MCP from marketplace...

Step 1: Downloading server (8.4 MB)
  [████████████████████] 100% - 2.3 MB/s

Step 2: Installing dependencies
  ✓ axios@1.6.0
  ✓ octokit@2.0.0
  ✓ dotenv@16.0.0

Step 3: Initial configuration
  Select authentication method:
    1) OAuth (recommended)
    2) Personal Access Token

  Enter choice [1]: 1

  Opening GitHub OAuth in browser... ✓
  Waiting for authorization...
  ✓ Authorization successful!

Step 4: Verification
  ✓ Server online
  ✓ Authentication valid
  ✓ Permissions verified
  ✓ 18,293 downloads, 4.9/5.0 rating

Installation Complete!
Location: ~/.mcp/servers/github
Config: ~/.mcp/config/github.json
Next: /mcp:configure github --set-default-repo <owner/repo>
```

### Batch Installation

```bash
/mcp:marketplace --install "github,postgres,slack,n8n"
```

Installs multiple servers in sequence.

## Browsing with Filters

### Complete Filter Workflow

```bash
/mcp:marketplace --category data --sort rating --limit 10
```

Output:

```
MCP Servers - Data Category (sorted by rating, showing top 10)

1. PostgreSQL MCP                                    ★★★★★ (1,456 reviews)
2. MongoDB MCP                                       ★★★★☆ (847 reviews)
3. Firebase MCP                                      ★★★★☆ (623 reviews)
...

Want more details? /mcp:marketplace --details postgres
Ready to install? /mcp:marketplace --install postgres
```

### Category-Based Discovery

```bash
/mcp:marketplace --category integration
```

Shows workflow automation and integration servers:

- n8n
- Make (formerly Integromat)
- Zapier
- IFTTT
- Pipedream

## Reviews & Community Feedback

### View User Reviews

```bash
/mcp:marketplace --details github --show-reviews
```

Output:

```
GitHub MCP - User Reviews (Showing 1-10 of 2,847)

★★★★★ "Best GitHub integration I've found"
By: @dev_architect on Nov 25, 2024
Setup was smooth, works perfectly with our CI/CD pipelines. We use it
to automate PR reviews and issue creation. Highly recommended!
Helpful votes: 342

★★★★★ "Essential for repo management"
By: @platform_engineer on Nov 20, 2024
Using this with /agent:route to manage 40+ repositories automatically.
Saved us hours on manual PR reviews. Great support from Anthropic team.
Helpful votes: 287

★★★☆☆ "Good but missing some features"
By: @devops_lead on Nov 18, 2024
Mostly works great, but wish it supported branch protection rules
automation. Requested feature in GitHub issues. Plan to update rating
when implemented.
Helpful votes: 156

[Showing 1-10 of 2,847 reviews | Page 1/285]
View older | View newest | View most helpful
```

## Compatibility & Requirements Checking

### Check Compatibility

```bash
/mcp:marketplace --details postgres --check-compatibility
```

Output:

```
PostgreSQL MCP - Compatibility Check
═════════════════════════════════════════════════════════════════════

Your System:
  OS: Linux (Ubuntu 20.04)
  Node.js: 18.0.0 ✅
  Python: 3.9.2 ✅
  Docker: Available ✅

Server Requirements:
  Python: 3.8+ ✅ (You have 3.9.2)
  psycopg2: Required (will be installed)
  PostgreSQL: 10+ (for usage, not installation)

Compatibility: ✅ FULLY COMPATIBLE

Dependencies to Install:
  + psycopg2-binary==2.9.9
  + python-dotenv==0.19.0

Space Required: 47 MB
Installation Time: ~2 minutes

Ready to install? /mcp:marketplace --install postgres
```

## Recommendations

### Smart Recommendations

```bash
/mcp:marketplace --recommend-for "automation"
```

Output:

```
MCP Servers Recommended for: Automation

Based on popular use cases:

Tier 1 - Essential (Most users install these first)
  1. n8n MCP (workflows)
  2. GitHub MCP (CI/CD integration)
  3. Slack MCP (notifications)

Tier 2 - Complementary (Popular add-ons)
  4. PostgreSQL MCP (data)
  5. Stripe MCP (payments)
  6. Google Drive MCP (files)

Tier 3 - Advanced (Power users)
  7. Custom API MCP
  8. Anthropic Docs MCP
  9. TypeScript Checker

Install all: /mcp:marketplace --install-bundle automation
Install custom: /mcp:marketplace --install "n8n,github,slack"
```

## Integration with Prompt Blueprint

### Markdown Documentation Generation

```bash
/mcp:marketplace --export-docs ~/MCP_MARKETPLACE.md
```

Generates comprehensive markdown with all servers, ratings, installation commands.

### Dashboard View

```bash
/ui:dashboard --marketplace
```

Opens web interface for browsing marketplace with visual filters and installation buttons.

## Related Commands

- `/mcp:install` - Install specific MCP server
- `/mcp:list` - View installed servers
- `/mcp:configure` - Configure server settings
- `/agent:route` - Route tasks to agents using MCP servers
- `/workflow:create` - Create workflows using MCP servers
- `/ui:dashboard` - Web-based marketplace browser
