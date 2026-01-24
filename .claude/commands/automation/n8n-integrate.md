---
description: Connect with n8n-mcp for visual workflow automation and advanced integrations
argument-hint: [--mode create|sync|import] [--workflow name] [--n8n-url url]
model: claude-3-5-haiku-20241022
allowed-tools: Bash, AskUserQuestion
---

# n8n Integration: Visual Workflow Automation

Connect with n8n-mcp server for powerful, visual workflow automation with 400+ integrations.

## Step 1: Check n8n-mcp Connection

Verify n8n-mcp server is available and properly configured:

```bash
# Check n8n server status
curl -s http://localhost:5678/api/v1/health

# Expected response:
# {
#   "status": "ok",
#   "message": "n8n is running"
# }
```

**n8n-mcp Features**:

- Visual workflow builder (drag-and-drop)
- 400+ pre-built integrations
- Custom code nodes (JavaScript, Python)
- Conditional logic and error handling
- Webhook triggers and scheduling
- Data transformation and mapping
- Real-time execution monitoring
- Webhook execution history

## Step 2: Determine Integration Mode

Choose how to work with n8n:

**Mode A: Create New Workflow in n8n**

- Design visually in n8n interface
- Use 400+ pre-built integrations
- Deploy and monitor from n8n dashboard
- Sync back to this automation system

**Mode B: Sync Existing Workflow**

- Take workflow from our automation system
- Convert to n8n format
- Push to n8n instance
- Manage in both systems

**Mode C: Import from n8n**

- Export existing n8n workflow
- Convert to our automation format
- Integrate with CRM and other tools
- Manage from here

## Step 3: Authentication Setup

Configure n8n-mcp authentication:

```yaml
n8n Configuration:
  Server URL: http://localhost:5678 (or your n8n instance)
  API Key: [stored securely]
  Webhook Base URL: https://your-domain.com/webhooks
  Timeout: 30 seconds
  Retry Policy: 3 attempts, exponential backoff
```

**Setup Steps**:

1. Get API key from n8n admin panel
2. Configure webhook base URL
3. Test connection to n8n
4. Authorize Zoho CRM access (for bidirectional sync)
5. Set up logging and monitoring

## Step 4: Available n8n Integrations

```
┌─────────────────────────────────────────────────────────┐
│          n8n SUPPORTED INTEGRATIONS (400+)              │
├─────────────────────────────────────────────────────────┤

CRM & Business:
  ✓ Zoho CRM, Salesforce, HubSpot, Pipedrive
  ✓ Zoho Mail, Gmail, Outlook, SendGrid
  ✓ Slack, Microsoft Teams, Discord
  ✓ Monday.com, Asana, Jira, Linear

Data & Storage:
  ✓ Google Sheets, Microsoft Excel, Airtable
  ✓ AWS S3, Google Cloud Storage, Azure Blob
  ✓ MySQL, PostgreSQL, MongoDB
  ✓ Firebase, Supabase

Payments & Finance:
  ✓ Stripe, PayPal, Square
  ✓ QuickBooks, Xero, FreshBooks
  ✓ TransferWise, Plaid

Communication:
  ✓ Twilio (SMS/Voice), Vonage
  ✓ SendGrid, Mailgun (Email)
  ✓ Telegram, WhatsApp Business

Automation & Integration:
  ✓ Zapier (bidirectional)
  ✓ Make (formerly Integromat)
  ✓ IFTTT
  ✓ Custom HTTP/REST APIs

Analytics & Reporting:
  ✓ Google Analytics, Mixpanel
  ✓ Segment, Datadog
  ✓ Grafana

[View Full Integration List]
```

## Step 5: Create New Workflow in n8n

**Example: Property Lead to CRM Automation**

```
STEP 1: Define Trigger
┌──────────────────────────────────┐
│  Webhook Trigger                 │
├──────────────────────────────────┤
│ Listen method: POST              │
│ Path: /property-lead             │
│ Response: Immediately            │
│ Expected fields:                 │
│ - name, email, phone             │
│ - property_id, move_in_date      │
└──────────────────────────────────┘

STEP 2: Validate Input
┌──────────────────────────────────┐
│  Set Node                        │
├──────────────────────────────────┤
│ Validate required fields:        │
│ - email (required)               │
│ - phone (required)               │
│ - property_id (required)         │
│                                  │
│ Extract move_in_date format      │
│ Default timezone: UTC            │
└──────────────────────────────────┘

STEP 3: Create CRM Lead
┌──────────────────────────────────┐
│  Zoho CRM Node                   │
├──────────────────────────────────┤
│ Action: Create Lead              │
│ Mapping:                         │
│  - First Name: ${name}           │
│  - Email: ${email}               │
│  - Phone: ${phone}               │
│  - Custom Field - Property: ID   │
│  - Move-in Date: ${move_in_date} │
│  - Source: Web Form              │
│                                  │
│ Output: Lead ID, Assignment info │
└──────────────────────────────────┘

STEP 4: Check Lead Status
┌──────────────────────────────────┐
│  IF Node (Conditional)           │
├──────────────────────────────────┤
│ IF: CRM field "Approval_Status"  │
│     == "Pre-Approved"            │
│                                  │
│  THEN: Auto-onboarding sequence  │
│  ELSE: Manual approval needed    │
└──────────────────────────────────┘

STEP 5a: Auto-Onboarding (Pre-Approved)
┌──────────────────────────────────┐
│  1. Create Tenant Account        │
│  2. Send Welcome Email           │
│  3. Generate Lease Documents     │
│  4. Schedule Walk-Through        │
│  5. Notify Property Manager      │
└──────────────────────────────────┘

STEP 5b: Manual Approval (Needs Review)
┌──────────────────────────────────┐
│  1. Route to Manager             │
│  2. Wait for approval (timeout)  │
│  3. If approved: continue Step 5a│
│  4. If rejected: notify applicant│
└──────────────────────────────────┘

STEP 6: Log & Notify
┌──────────────────────────────────┐
│  Update CRM Activity             │
│  Send Slack Notification         │
│  Store in Google Sheets (report) │
└──────────────────────────────────┘
```

## Step 6: Visual Workflow Builder

n8n provides drag-and-drop interface:

```
┌────────────────────────────────────────────────────────┐
│  n8n Visual Workflow Builder                            │
├────────────────────────────────────────────────────────┤
│                                                        │
│  [Webhook]                                            │
│     │                                                 │
│     ▼                                                 │
│  [Validate]                                           │
│     │                                                 │
│     ▼                                                 │
│  [Zoho CRM: Create Lead]                              │
│     │                                                 │
│     ├─▶ [IF: Approved?]                              │
│     │       ├─▶ [Auto-Onboard] ─▶ [Notify Manager]  │
│     │       └─▶ [Needs Review] ─▶ [Wait Approval]    │
│     │                                                 │
│     ▼                                                 │
│  [Slack Notification]                                │
│     │                                                 │
│     ▼                                                 │
│  [Google Sheets: Log]                                │
│                                                        │
└────────────────────────────────────────────────────────┘
```

**Key Features**:

- Drag nodes from 400+ library
- Connect nodes with lines
- Configure each node visually
- Test with sample data
- See execution in real-time
- Full execution history

## Step 7: Test Workflow

Run test executions before deploying:

```bash
# Test with sample webhook data
POST http://localhost:5678/webhook/property-lead

{
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "555-1234",
  "property_id": "PROP-001",
  "move_in_date": "2025-03-01"
}

# Check execution result
Status: ✓ Success
Execution Time: 1.2 seconds
Actions Completed:
  ✓ CRM lead created (Lead ID: L-12345)
  ✓ Email sent (1.2s)
  ✓ Slack notification sent (0.8s)
  ✓ Logged in Google Sheets (0.9s)

Output Data:
{
  "lead_id": "L-12345",
  "crm_status": "New",
  "approval_status": "Pre-Approved",
  "onboarding_url": "https://tenant-portal.example.com/..."
}
```

## Step 8: Deploy & Activate

```yaml
Pre-Deployment Checklist:
  ✓ All nodes configured
  ✓ Test execution passed
  ✓ Error handling configured
  ✓ Webhook URL noted
  ✓ Rate limits set
  ✓ Timeout values configured
  ✓ Logging enabled
  ✓ Monitoring alerts set

Deployment Steps:
  1. Activate workflow in n8n dashboard
  2. Get webhook URL
  3. Add to form/external system
  4. Test live execution
  5. Set up monitoring
  6. Configure alerts

Production Checklist:
  ✓ Webhook URL added to production forms
  ✓ Error notification channel configured
  ✓ Success metrics tracked
  ✓ Backup/rollback plan ready
```

## Step 9: Webhook URL & Integration

After workflow activated, get webhook URL:

```
WEBHOOK URL:
https://your-n8n-instance.com/webhook/property-lead-abc123

Use in HTML Form:
<form action="https://your-n8n-instance.com/webhook/property-lead-abc123"
      method="POST">
  <input type="text" name="name" required>
  <input type="email" name="email" required>
  <input type="tel" name="phone" required>
  <input type="text" name="property_id" required>
  <input type="date" name="move_in_date" required>
  <button type="submit">Submit</button>
</form>

Use in JavaScript:
fetch('https://your-n8n-instance.com/webhook/property-lead-abc123', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    name: formData.name,
    email: formData.email,
    phone: formData.phone,
    property_id: formData.property_id,
    move_in_date: formData.move_in_date
  })
})

Use with Zapier/Make:
Configure webhook action with above URL
Map fields from trigger
Test execution
Activate
```

## Step 10: Monitoring & Alerts

Set up n8n monitoring:

```bash
# View workflow execution history
GET http://localhost:5678/api/v1/executions?workflow_id=ABC123

# Configure monitoring
- Error rate threshold: Alert if > 5%
- Execution time: Alert if > 30s (timeout)
- Failed executions: Alert immediately
- Success rate: Track daily/weekly

# Alert Channels:
- Email to workflow owner
- Slack to #automation-alerts
- SMS for critical failures
- Dashboard metrics
```

**Example Dashboard Metrics**:

```
Workflow: Property Lead Automation
Time Period: Last 24 hours

Total Executions: 47
Success Rate: 97.9% (46/47)
Average Execution Time: 1.8 seconds
Fastest: 0.9 seconds
Slowest: 4.2 seconds

By Status:
✓ Success: 46 (97.9%)
⚠ Warning: 1 (2.1%)
✗ Error: 0 (0%)

Top Integration:
- Zoho CRM: 47 executions
- Email: 46 executions
- Slack: 46 executions
- Google Sheets: 46 executions

Failed Execution Details:
ID: exec-123456
Time: 14:32:15 UTC
Error: Slack notification timeout
Retry: Auto-retry in 30 seconds
Status: Resolved

Recent Logs:
14:45:32 - Lead created successfully
14:44:15 - CRM API responded in 0.8s
14:43:02 - Webhook received from form
```

## Step 11: Sync with Local Automation System

**Option A: Import n8n Workflow Here**

```bash
# Export from n8n
1. Open workflow in n8n
2. Click Export
3. Save JSON file

# Convert to our format
/automation:import-n8n property-lead-automation.json

# Result:
✓ Workflow imported and converted
✓ Integrated with Zoho CRM
✓ Available as: /automation:test-workflow property-lead-automation
✓ Can be edited visually
```

**Option B: Sync Changes Between Systems**

```yaml
Bidirectional Sync:
  On n8n side:
    - Edit workflow visually
    - Click "Sync to Automation Hub"
    - Changes pushed automatically

  On Automation Hub side:
    - Edit configuration
    - Click "Sync to n8n"
    - Updates pushed to n8n

Sync Status:
  - Last synced: 2025-01-15 14:32:15
  - Status: In sync
  - Pending changes: None
```

## Step 12: Advanced Features

### Custom Code Nodes

```javascript
// In n8n Custom Function Node
// Transform data before sending to CRM

const lead_data = items[0].json;

// Validate and clean data
lead_data.name = lead_data.name.trim().toUpperCase();
lead_data.phone = lead_data.phone.replace(/\D/g, '');
lead_data.move_in_date = new Date(lead_data.move_in_date).toISOString();

// Add computed fields
lead_data.source_system = 'Web Form';
lead_data.created_at = new Date().toISOString();
lead_data.assigned_to = 'PROP-' + lead_data.property_id;

return [{ json: lead_data }];
```

### Error Handling & Retries

```yaml
Error Handling Strategy:
  Timeout Error (request takes > 30s):
    - Retry: 3 times (wait 10s between)
    - If still fails: Log and continue
    - Alert: Email to admin

  Rate Limit (429):
    - Retry: 5 times (exponential backoff)
    - Wait: 60 seconds between attempts
    - Alert: Slack notification

  Authentication Error (401):
    - Stop execution
    - Alert: Email + SMS to admin
    - Action: Manual intervention needed

  Server Error (5xx):
    - Retry: 3 times (wait 30s between)
    - Alert: Escalate if persists
```

### Scheduled Execution

```yaml
Schedule Options:
  Every hour:
    - Sync property updates from CRM
    - Generate daily report

  Every day at 9 AM:
    - Send morning briefing
    - Process pending approvals

  Every Monday:
    - Send weekly performance report
    - Check for overdue tasks

Timezone: User's local timezone
Backoff: Handle missed executions
```

## Property Management Workflow Examples with n8n

### Example 1: Lead-to-Tenant Complete Flow

```
Webhook (Form) → Validate → CRM Create
→ Check Status → [IF Pre-Approved: Auto-Onboard | ELSE: Wait Approval]
→ Tenant Portal Setup → Lease Documents
→ Email + SMS → Slack → Google Sheets Log
→ 404 Success Notification
```

### Example 2: Maintenance Request with AI

```
Webhook (Mobile) → Extract Request
→ OpenAI (Categorize & Prioritize)
→ CRM Create Ticket
→ [IF Urgent: Immediate | ELSE: Queue]
→ Assign Contractor → Send Work Order
→ Wait for Completion → Collect Photo
→ Verify → Invoice → Tenant Feedback
```

### Example 3: Rent Collection with Accounting Sync

```
Scheduled (1st of month) → Generate Invoice
→ Send Email + SMS → Wait for Payment
→ Check Payment Status → Receipt → CRM Update
→ QuickBooks Sync → Generate Report
→ Dashboard Update → Success Alert
```

---

**Uses**: n8n-mcp-server, workflow-visualization-engine
**Model**: Haiku (fast n8n operations)
**n8n Features**: 400+ integrations, visual builder, webhooks, scheduling
**Typical Setup Time**: 10-30 minutes depending on complexity
