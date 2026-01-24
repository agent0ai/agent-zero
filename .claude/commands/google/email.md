---
description: Gmail management - send, read, search emails with AI-powered triage workflows
argument-hint: <action> [--to <email>] [--subject <text>] [--body <text>] [--search <query>]
model: claude-3-5-haiku-20241022
allowed-tools:
  - Bash
  - Read
  - Write
  - AskUserQuestion
---

# Gmail Management Command

## Overview

Manage Gmail operations through both atomic MCP operations (<1 second) and orchestrated n8n workflows. Integrates with morning routine for automated email triage.

## Actions

### Atomic Operations (via MCP)

**send** - Send email

```bash
/google:email send --to "client@example.com" --subject "Project Update" --body "..."
```

**read** - Read emails

```bash
/google:email read --unread
/google:email read --from "tenant@example.com"
```

**search** - Search emails

```bash
/google:email search "from:tenant subject:maintenance"
/google:email search "is:unread after:2025/01/15"
```

**label** - Apply Gmail labels

```bash
/google:email label --email-id <id> --label "Action Required"
```

### Orchestrated Workflows (via n8n)

**triage** - Morning email categorization (see `/email:triage`)

```bash
/google:email triage
```

## Implementation Details

### MCP Server Required

This command requires **Composio MCP** or **Gmail MCP** to be installed:

```bash
# Install Composio MCP (recommended - includes Gmail, Calendar, Drive)
/mcp:install composio --auth-type oauth

# Or install Gmail MCP standalone
/mcp:install gmail --auth-type oauth
```

### Authentication

Uses OAuth 2.0 for secure Gmail access:

- Scopes: `gmail.send`, `gmail.readonly`, `gmail.modify`, `gmail.labels`
- Credentials stored in `~/.mcp/auth/composio.json` (encrypted)
- Auto-refresh tokens managed by MCP server

### Context Integration

Automatically uses credentials from active context:

```json
{
  "name": "property-management",
  "integrations": {
    "google_workspace": {
      "enabled": true,
      "email": "manager@mainstreetproperties.com",
      "mcp_server": "composio"
    }
  }
}
```

## Step-by-Step Execution

### Action: send

1. **Validate Inputs**
   - Verify recipient email format
   - Check subject is not empty (warn if missing)
   - Confirm body content exists

2. **Approval Workflow** (if enabled in context)

   ```
   ┌─────────────────────────────────────────┐
   │  EMAIL PREVIEW                          │
   ├─────────────────────────────────────────┤
   │  From: manager@mainstreetproperties.com │
   │  To: tenant@example.com                 │
   │  Subject: Maintenance Update            │
   ├─────────────────────────────────────────┤
   │  Body:                                  │
   │  Hi John,                               │
   │                                         │
   │  The HVAC repair is scheduled for       │
   │  tomorrow at 2 PM. Please ensure        │
   │  access to the unit.                    │
   │                                         │
   │  Thanks,                                │
   │  Management                             │
   └─────────────────────────────────────────┘

   Send this email? (y/n)
   ```

3. **Send via MCP**

   ```javascript
   // Call Composio MCP Gmail API
   const result = await mcp.gmail.send({
     to: recipient,
     subject: subject,
     body: body,
     from: context.integrations.google_workspace.email
   });
   ```

4. **Confirmation**

   ```
   ✓ Email sent successfully
   Message ID: <msg_abc123>
   Sent at: 2025-01-20 14:32:15

   Auto-saved to /knowledge/sent-emails/2025-01-20-maintenance-update.md
   ```

### Action: search

1. **Parse Search Query**
   - Support Gmail search operators
   - Common shortcuts: `unread`, `important`, `from:X`, `subject:Y`

2. **Execute Search via MCP**

   ```javascript
   const results = await mcp.gmail.search({
     query: searchQuery,
     maxResults: 50
   });
   ```

3. **Display Results**

   ```
   Found 12 emails matching "from:tenant subject:maintenance"

   [1] 🔴 URGENT: Water leak in Unit 2B
       From: john.doe@example.com
       Date: Jan 20, 2:15 PM
       Preview: The kitchen sink is leaking and water is...

   [2] 📋 Scheduled maintenance reminder
       From: jane.smith@example.com
       Date: Jan 19, 4:30 PM
       Preview: Just a reminder that the HVAC inspection...

   [3] ✅ Maintenance completed - Unit 4A
       From: maintenance@contractor.com
       Date: Jan 18, 11:20 AM
       Preview: We completed the window repair in Unit 4A...

   Actions: [r]ead, [a]rchive, [l]abel, [d]elete, [q]uit
   ```

### Action: triage

This is a complex workflow - see `/email:triage` command for full details.

Quick overview:

1. Fetch overnight emails (MCP)
2. AI categorize by urgency/importance
3. Generate summary dashboard
4. Integrate with morning routine

## Integration with Existing Commands

### With /knowledge:capture

Auto-save sent emails to knowledge base:

```bash
# Automatically triggered after sending email
/knowledge:capture --source gmail --type email --id <msg_id>
```

### With /context:switch

Each context loads its own Gmail account:

```bash
/context:switch property-management
# Now using: manager@mainstreetproperties.com

/context:switch consulting-client
# Now using: consultant@acmecorp.com
```

### With /meeting:prep

Search for email threads related to upcoming meeting:

```bash
/meeting:prep "Team Standup"
# Automatically searches: from:team@ subject:"standup" OR "team meeting"
```

### With /email:triage

Morning email workflow:

```bash
/email:triage
# Uses /google:email search and read operations
```

## Business Value

**Time Savings**:

- Email sending: 30 seconds vs 2-3 minutes (traditional)
- Email search: <1 second vs 30-60 seconds (Gmail UI)
- Email triage: 5 minutes vs 30-45 minutes (manual)
- **Total**: 30-60 minutes/day = 3-5 hours/week

**Productivity Gains**:

- CLI-first workflow (no context switching to browser)
- AI-powered categorization and summarization
- Automatic knowledge capture
- Context-aware multi-account management

**ROI**:

- Time saved: 4 hrs/week × $150/hr = $600/week = **$30,000/year**
- Reduced email anxiety: Priceless

## Success Metrics

✅ Email operations complete in <1 second (atomic)
✅ Zero authentication failures (auto-refresh)
✅ 100% email delivery success rate
✅ Inbox zero achievable 5+ days/week (with triage)
✅ Context switching works flawlessly

## Security & Privacy

- OAuth 2.0 for authentication (no password storage)
- Encrypted credential storage (~/.mcp/auth/)
- Per-context email isolation
- Audit logging of all operations
- Automatic token refresh
- Revocation support

## Troubleshooting

### MCP Server Not Installed

```bash
Error: Composio MCP server not found

Solution:
/mcp:install composio --auth-type oauth
```

### Authentication Failed

```bash
Error: Gmail authentication expired

Solution:
/mcp:configure composio --refresh-auth
# Opens browser for re-authentication
```

### Rate Limit Exceeded

```bash
Error: Gmail API rate limit exceeded (quota: 250/min)

Solution:
# Wait 60 seconds or upgrade Gmail API quota
# Check usage: /mcp:list --monitor
```

### Wrong Gmail Account

```bash
Error: Sending from wrong account

Solution:
# Verify active context
/context:current

# Switch to correct context
/context:switch property-management
```

## Advanced Options

### Batch Operations

```bash
# Send to multiple recipients
/google:email send --to "tenant1@x.com,tenant2@x.com" --subject "Update"

# Search and label in bulk
/google:email search "is:unread older_than:7d" | /google:email label --label "Archive"
```

### Templates

```bash
# Use email template
/google:email send --template "lease-renewal" --to "tenant@x.com" --vars "name=John,unit=2B"
```

### Scheduling

```bash
# Schedule email for later (requires n8n workflow)
/google:email send --to "tenant@x.com" --subject "Reminder" --schedule "2025-01-25 09:00"
```

### AI Composition

```bash
# AI-generated email
/google:email send --to "tenant@x.com" --generate "Politely ask about rent payment that is 5 days overdue"
```

## Related Commands

- `/email:triage` - Morning email workflow automation
- `/google:calendar` - Calendar management
- `/google:drive` - File management
- `/knowledge:capture` - Save emails to knowledge base
- `/context:switch` - Switch between email accounts
- `/meeting:prep` - Meeting preparation with email search

## Notes

**Performance**: Atomic operations via MCP complete in <1 second. Workflows via n8n may take 5-30 seconds depending on complexity.

**Reliability**: 99.9%+ uptime when using MCP servers. Gmail API itself has 99.95% SLA.

**Scalability**: Supports unlimited email accounts via context switching. Each context can have different Gmail credentials.

---

*Transform email from a productivity drain into a superpower with AI-assisted Gmail management.*
