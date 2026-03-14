# Email Tool - Agent Jumbo Documentation

## Overview

The Email tool provides comprehensive email capabilities for Agent Jumbo, enabling automated communication, customer engagement, and team notifications. It integrates SMTP sending with existing IMAP reading functionality.

## Features

- **Send Emails**: SMTP-based email sending with attachment support
- **Read Emails**: IMAP-based inbox monitoring and message retrieval
- **Search Emails**: Advanced filtering and search capabilities
- **Bulk Sending**: Rate-limited mass email with delivery tracking

## Configuration

### Environment Variables (Required)

```bash
# Gmail SMTP Configuration
GMAIL_FROM_EMAIL="your-email@gmail.com"
GMAIL_APP_PASSWORD="your-16-char-app-password"
GMAIL_SMTP_SERVER="smtp.gmail.com"  # Optional, defaults to smtp.gmail.com
GMAIL_SMTP_PORT="587"  # Optional, defaults to 587

# Gmail IMAP Configuration (for reading)
GMAIL_IMAP_SERVER="imap.gmail.com"  # Optional, defaults to imap.gmail.com
GMAIL_IMAP_PORT="993"  # Optional, defaults to 993
```

### Gmail App Password Setup

1. Enable 2-Factor Authentication on your Google Account
2. Go to [Google Account Security](https://myaccount.google.com/security)
3. Select "App passwords" under "2-Step Verification"
4. Generate new app password for "Mail" and "Other (Custom name)"
5. Copy the 16-character password (no spaces)
6. Add to your `.env` file as `GMAIL_APP_PASSWORD`

## Available Actions

### 1. Send Email

Send individual emails with full formatting and attachment support.

**Action:** `send`

**Parameters:**

- `to` (required): Email address(es) - string or list
- `subject` (required): Email subject line
- `body` (required): Email content (plain text or HTML)
- `cc` (optional): CC recipients - string or list
- `bcc` (optional): BCC recipients - string or list
- `attachments` (optional): List of file paths to attach
- `html` (optional): Boolean, set to `true` for HTML emails (default: false)
- `from_name` (optional): Display name for sender (default: "Agent Jumbo")

**Example:**

```json
{
  "action": "send",
  "to": "customer@example.com",
  "subject": "Your Project Proposal",
  "body": "Dear Customer,\n\nPlease find attached your customized proposal...",
  "attachments": ["tmp/proposals/customer_proposal_v1.pdf"],
  "from_name": "AI Solutions Team"
}
```

**HTML Email Example:**

```json
{
  "action": "send",
  "to": ["stakeholder1@company.com", "stakeholder2@company.com"],
  "cc": "manager@company.com",
  "subject": "Weekly Progress Report",
  "body": "<h2>Project Update</h2><p>Tasks completed this week:</p><ul><li>Feature A deployed</li><li>Testing completed</li></ul>",
  "html": true
}
```

### 2. Read Emails

Retrieve emails from inbox with filtering options.

**Action:** `read`

**Parameters:**

- `filter` (optional): Dictionary of filter criteria
  - `unread`: Boolean, read only unread messages (default: true)
  - `sender`: Filter by sender email address
  - `subject`: Filter by subject keywords
  - `since_date`: Messages since date (format: "DD-MMM-YYYY")
- `download_folder` (optional): Where to save attachments (default: "tmp/email/inbox")

**Example:**

```json
{
  "action": "read",
  "filter": {
    "unread": true,
    "sender": "client@company.com"
  },
  "download_folder": "tmp/customer_emails"
}
```

### 3. Search Emails

Advanced email search with multiple criteria.

**Action:** `search`

**Parameters:**

- `sender` (optional): Filter by sender email
- `subject` (optional): Filter by subject keywords
- `unread_only` (optional): Boolean, only unread messages
- `since_date` (optional): Messages since date

**Example:**

```json
{
  "action": "search",
  "sender": "support@example.com",
  "subject": "urgent",
  "unread_only": true
}
```

### 4. Send Bulk Emails

Send multiple emails with rate limiting to avoid spam detection.

**Action:** `send_bulk`

**Parameters:**

- `recipients` (required): List of email configurations
  - Each item is a dict with: `to`, `subject`, `body`, `attachments`, `html`
- `delay_seconds` (optional): Delay between sends (default: 0.5)

**Example:**

```json
{
  "action": "send_bulk",
  "recipients": [
    {
      "to": "client1@example.com",
      "subject": "Your Custom Proposal",
      "body": "Dear Client 1...",
      "attachments": ["tmp/proposals/client1_proposal.pdf"]
    },
    {
      "to": "client2@example.com",
      "subject": "Your Custom Proposal",
      "body": "Dear Client 2...",
      "attachments": ["tmp/proposals/client2_proposal.pdf"]
    }
  ],
  "delay_seconds": 1.0
}
```

## Integration Examples

### Customer Lifecycle Integration

Automatically send proposals when generated:

```json
{
  "tool": "email",
  "action": "send",
  "to": "{{customer_email}}",
  "subject": "Your Custom AI Solution Proposal",
  "body": "Dear {{customer_name}},\n\nThank you for your interest. Please find your customized proposal attached.\n\nBest regards,\nAI Solutions Team",
  "attachments": ["{{proposal_path}}"],
  "html": false
}
```

### Virtual Team Integration

Send task assignment notifications:

```json
{
  "tool": "email",
  "action": "send",
  "to": "{{team_member_email}}",
  "subject": "New Task Assignment: {{task_title}}",
  "body": "<h2>Task Assignment</h2><p><strong>Task:</strong> {{task_title}}</p><p><strong>Due:</strong> {{due_date}}</p><p><strong>Priority:</strong> {{priority}}</p><p>Please review and confirm.</p>",
  "html": true
}
```

### Daily Digest Example

Send summary of activities:

```json
{
  "tool": "email",
  "action": "send",
  "to": ["manager@company.com", "stakeholder@company.com"],
  "subject": "Daily Activity Digest - {{date}}",
  "body": "<h2>Today's Summary</h2><ul><li>New leads: {{lead_count}}</li><li>Proposals sent: {{proposal_count}}</li><li>Tasks completed: {{task_count}}</li></ul>",
  "html": true
}
```

## Use Cases

### 1. Automated Proposal Delivery

- Generate proposal document with customer_lifecycle tool
- Send via email with attachment
- Track email opens/responses
- Follow up automatically after 3 days

### 2. Team Collaboration Notifications

- Task assigned → Email notification to assignee
- Task completed → Email update to stakeholders
- Daily digest → Summary to managers

### 3. Customer Communication

- Welcome emails for new leads
- Proposal follow-ups
- Project status updates
- Invoice delivery

### 4. Multi-Account Management (Future Phase 2)

- <sales@company.com> for client proposals
- <support@company.com> for customer service
- <dev@company.com> for technical communications
- Each with separate OAuth2 credentials

## Error Handling

The tool provides detailed error messages for common issues:

- **Missing Credentials**: "Email credentials not configured..."
- **Invalid Email**: "Invalid email addresses: ..."
- **Send Failure**: Shows error type and details
- **IMAP Connection**: Shows server/authentication errors

## Rate Limits

Gmail SMTP has built-in limits:

- **Daily limit**: 500 emails per day (personal), 2000 (Google Workspace)
- **Burst limit**: ~100-150 emails per batch
- **Recommendation**: Use 0.5-1.0 second delays for bulk sending

## Security Considerations

1. **App Passwords**: More secure than account password, can be revoked anytime
2. **Environment Variables**: Never commit credentials to Git
3. **TLS Encryption**: All SMTP connections use STARTTLS
4. **Attachment Validation**: Filenames sanitized to prevent path traversal

## Future Enhancements (Phase 2 - Gmail API)

Planned features with OAuth2:

- Multi-account support with separate credentials
- Email labeling and categorization
- Draft management
- Advanced search with Gmail query syntax
- Push notifications via Pub/Sub
- Read receipts and tracking
- Calendar integration

## Troubleshooting

### "Email credentials not configured"

→ Add GMAIL_FROM_EMAIL and GMAIL_APP_PASSWORD to .env

### "Authentication failed"

→ Verify app password is correct (16 characters, no spaces)
→ Ensure 2FA is enabled on Google Account

### "Invalid email addresses"

→ Check email format (must contain @ and valid domain)

### "Connection timeout"

→ Check internet connection
→ Verify SMTP server (smtp.gmail.com) and port (587)
→ Check firewall/proxy settings

### "Quota exceeded"

→ You've hit Gmail's daily sending limit (500/day)
→ Wait 24 hours or upgrade to Google Workspace

## Examples for Common Workflows

### Send Welcome Email

```json
{
  "tool": "email",
  "action": "send",
  "to": "newcustomer@example.com",
  "subject": "Welcome to AI Solutions!",
  "body": "Welcome! We're excited to work with you...",
  "from_name": "AI Solutions Onboarding"
}
```

### Check for Customer Responses

```json
{
  "tool": "email",
  "action": "read",
  "filter": {
    "unread": true,
    "sender": "customer@example.com",
    "since_date": "01-Jan-2025"
  }
}
```

### Send Proposal with Attachments

```json
{
  "tool": "email",
  "action": "send",
  "to": "prospect@bigcorp.com",
  "subject": "AI Implementation Proposal - BigCorp",
  "body": "Please review the attached proposal and technical specifications.",
  "attachments": [
    "tmp/proposals/bigcorp_proposal.pdf",
    "tmp/proposals/bigcorp_technical_specs.pdf"
  ]
}
```

## Best Practices

1. **Always validate email addresses** before sending
2. **Use HTML sparingly** - many clients prefer plain text
3. **Keep attachments under 25MB** (Gmail limit)
4. **Use descriptive subjects** for better tracking
5. **Add delays in bulk sending** to avoid spam filters
6. **Monitor unread emails** regularly to catch customer responses
7. **Use BCC for mass emails** to protect recipient privacy
8. **Test with your own email** before sending to customers
