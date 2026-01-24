---
description: Visual workflow builder with drag-and-drop logic for process automation
argument-hint: <workflow-name> [--template property-management|crm-sync|maintenance] [--steps number]
model: claude-3-5-haiku-20241022
allowed-tools: Bash, AskUserQuestion
---

# Create Workflow: **${ARGUMENTS:-my-workflow}**

## Step 1: Collect Workflow Requirements

Ask user to clarify workflow intent:

**Workflow Name**: `${ARGUMENTS}`

**Questions**:

1. What's the primary purpose of this workflow?
2. Which systems/tools should it integrate with?
3. How many steps do you need (estimate)?
4. What's the expected frequency? (on-demand, scheduled, event-triggered)
5. Who are the key stakeholders/approvers?

## Step 2: Select Workflow Template

**Available Templates** for quick start:

### A. Property Management Workflows

- **Lead to Tenant**: Web form → CRM lead → Property assignment → Tenant onboarding
- **Maintenance Request**: Mobile upload → CRM ticket → Slack notification → Completion tracking
- **Rent Collection**: Payment trigger → CRM update → Tenant receipt → Accounting sync
- **Property Listing**: Form → Photos/docs upload → MLS listing → Social media posts

### B. CRM Sync Workflows

- **Contact Sync**: Form submission → Zoho CRM → Email campaign → Tracking
- **Lead Scoring**: CRM input → Analysis → Lead ranking → Notification
- **Deal Pipeline**: Opportunity creation → Automated follow-up → Forecasting
- **Customer Success**: New customer → Onboarding sequence → Check-in schedule

### C. Document & Approval Workflows

- **Contract Approval**: Document upload → Reviewer routing → Signature flow → Archival
- **Expense Reporting**: Receipt scan → Category classification → Manager approval → Accounting
- **Content Workflow**: Draft → Review → Approval → Publishing → Distribution

### D. Communication Workflows

- **Notification Hub**: Trigger events → Message routing → Multi-channel send → Delivery tracking
- **Customer Support**: Ticket intake → Routing → Response → Satisfaction survey
- **Team Coordination**: Task creation → Assignment → Progress updates → Completion

### E. Data Integration Workflows

- **Data Sync**: Source system → Transformation → Target system → Validation
- **Report Generation**: Data collection → Aggregation → Formatting → Distribution
- **Backup & Archive**: Source data → Compression → Storage → Verification

## Step 3: Build Workflow Canvas

### Visual Workflow Structure

```
┌─────────────────────────────────────────────────────────┐
│                 WORKFLOW CANVAS                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  [START] → [Step 1] → [Decision] → [Step 2] → [END]   │
│              ↓                        ↓                 │
│           [Data]                  [Action]              │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Workflow Components

#### 1. Triggers (How workflow starts)

- **Webhook**: External system posts data
- **Schedule**: Runs on fixed interval (hourly, daily, weekly)
- **Event**: Triggered by system event (CRM record created, form submitted)
- **Manual**: User clicks button to run
- **Poll**: Checks external system periodically

#### 2. Actions (What the workflow does)

- **API Call**: HTTP request to external service
- **CRM Operation**: Create/update/delete in Zoho CRM
- **Send Email**: Via Zoho Mail or SMTP
- **Send SMS**: Via Zoho SMS or Twilio
- **Database**: Query/insert/update/delete records
- **File Operation**: Upload/download/transform files
- **Notification**: Internal alerts and dashboards

#### 3. Logic (How workflow decides)

- **Condition**: If/Then/Else based on data values
- **Switch**: Multiple branches based on field value
- **Loop**: Repeat actions for each item in list
- **Wait**: Pause until condition met (timeout supported)
- **Error Handling**: Catch and retry failed steps

#### 4. Integrations (Systems workflow connects to)

- **Zoho CRM**: Lead, contact, deal, activity operations
- **Zoho Mail**: Send emails with templates
- **Zoho SMS**: Send SMS messages
- **Google Sheets**: Read/write spreadsheet data
- **Slack**: Post messages and notifications
- **Zapier**: Pass data to Zapier workflows
- **Custom HTTP**: REST API endpoints
- **Webhook**: Receive data from external systems

## Step 4: Define Workflow Steps

**Example: Lead to Tenant Workflow**

### Step 1: Receive Property Lead

```
Trigger: Webhook
  - Listens on: /webhook/property-lead
  - Expected fields: name, email, phone, property_id, move_in_date
  - Validation: All required fields present
```

### Step 2: Create CRM Lead

```
Action: Zoho CRM - Create Lead
  - Input mapping:
    - Full Name: ${name}
    - Email: ${email}
    - Phone: ${phone}
    - Property Interest: ${property_id}
  - Assignment: Auto-assign to property agent
  - Output: Lead ID, Assignment details
```

### Step 3: Check Tenant Status

```
Logic: Condition
  - If: Application Status = "Pre-Approved"
    - Go to: Step 4 (Automated onboarding)
  - Else:
    - Go to: Step 5 (Manual review)
```

### Step 4: Automated Onboarding

```
Action: Multi-step sequence
  - Send welcome email
  - Create tenant portal access
  - Generate lease documents
  - Schedule walk-through
  - Create calendar events
  - Notify property manager
```

### Step 5: Manual Review

```
Action: Approval Flow
  - Route to: Property manager
  - Approval timeout: 24 hours
  - If approved: Continue to Step 4
  - If rejected: Notify applicant, close lead
```

### Step 6: Log Completion

```
Action: Update CRM
  - Set status: Tenant Onboarded
  - Set completion date: ${today}
  - Create activity log entry
  - Notify stakeholders
```

## Step 5: Configure Step Details

For each step, configure:

**Trigger Steps**:

- [ ] Trigger type selected
- [ ] Endpoint/schedule defined
- [ ] Authentication configured
- [ ] Payload schema validated
- [ ] Test trigger successful

**Action Steps**:

- [ ] Service/system selected
- [ ] Required credentials available
- [ ] Input fields mapped
- [ ] Error handling configured
- [ ] Success criteria defined
- [ ] Output variables named

**Logic Steps**:

- [ ] Condition/switch rules clear
- [ ] All branches have exit paths
- [ ] Loop termination condition defined
- [ ] Timeout values set
- [ ] Error paths handled

**Integration Steps**:

- [ ] API credentials stored securely
- [ ] Rate limits configured
- [ ] Retry logic enabled
- [ ] Timeout handling set
- [ ] Error messages logged

## Step 6: Add Error Handling & Retries

Configure for each action:

```yaml
Error Handling:
  - Network timeout: Retry 3 times, wait 10s between
  - Rate limit (429): Retry 5 times, exponential backoff
  - Auth failure (401): Stop, log error, alert admin
  - Bad request (400): Stop, log full payload, alert developer
  - Server error (500): Retry 3 times, wait 30s between

Timeout Settings:
  - Step timeout: 30 seconds
  - Overall workflow timeout: 5 minutes
  - Long-running async tasks: 24 hours max

Logging:
  - Log all inputs and outputs
  - Log execution time per step
  - Log all errors with full context
  - Archive old logs monthly
```

## Step 7: Set Up Approval Gates (if needed)

For workflows requiring human approval:

```
Approval Gate Configuration:
  - When triggered: On high-value operations
  - Approvers: Role-based (Manager, Finance, Legal)
  - Timeout: Auto-approve/reject after 24 hours
  - Notification: Email, Slack, in-app alert
  - Override: Emergency fast-track available
```

**Examples**:

- Property lease amount > $10,000 → Finance approval required
- New tenant with credit score < 650 → Manager approval required
- Payment refund > $500 → Finance + Manager approval required

## Step 8: Configure Notifications

Set up alerts for workflow status:

```yaml
Success Notification:
  - Channels: Email, Slack, SMS
  - Recipients: Workflow owner, primary stakeholder
  - Content: Summary of completed actions
  - Frequency: On completion

Failure Notification:
  - Channels: Email, Slack, SMS (urgent)
  - Recipients: Workflow owner, escalation manager
  - Content: Full error details, recovery steps
  - Frequency: Immediate

Scheduled Reports:
  - Daily: Workflows run, success rate, failures
  - Weekly: Performance metrics, trends
  - Monthly: ROI analysis, improvement opportunities
```

## Step 9: Testing & Validation

### 9a. Unit Tests (Individual Steps)

```bash
# Test trigger
curl -X POST http://localhost:3000/webhook/property-lead \
  -H "Content-Type: application/json" \
  -d '{"name":"John Doe","email":"john@example.com",...}'

# Test CRM integration
POST /crm/leads/create
{
  "first_name": "John",
  "last_name": "Doe",
  "email": "john@example.com",
  "phone": "555-1234"
}

# Test conditional logic
Input: {"app_status": "Pre-Approved"}
Expected: Route to "Automated Onboarding"
```

### 9b. Integration Tests (Full Workflow)

```bash
# End-to-end test
1. Submit test lead via webhook
2. Verify CRM lead created
3. Verify email sent
4. Verify tenant portal access granted
5. Verify property manager notified
6. Check completion status updated
```

### 9c. Performance Testing

```bash
# Load test: 100 simultaneous leads
# Success rate target: 99.9%
# Average execution time target: < 2 minutes
# Peak queue time: < 5 seconds
```

## Step 10: Deployment & Activation

```yaml
Pre-Deployment Checklist:
  - [ ] All steps tested individually
  - [ ] End-to-end test passed
  - [ ] Error handling verified
  - [ ] Performance targets met
  - [ ] Approval workflow configured
  - [ ] Notifications tested
  - [ ] Logging enabled
  - [ ] Documentation complete
  - [ ] Stakeholders trained
  - [ ] Rollback plan defined

Deployment Steps:
  1. Deploy to staging environment
  2. Run full test suite
  3. Get stakeholder sign-off
  4. Deploy to production
  5. Monitor for 24 hours
  6. Collect user feedback
  7. Optimize based on metrics

Activation Options:
  - [ ] Activate immediately (all users)
  - [ ] Activate with percentage rollout (start 10%, ramp to 100%)
  - [ ] Activate for specific users/groups only
  - [ ] Schedule activation for specific time
```

## Step 11: Display Workflow Summary

```
═══════════════════════════════════════════════════════════
                    WORKFLOW CREATED
═══════════════════════════════════════════════════════════

WORKFLOW NAME: Lead to Tenant Automation
STATUS: Ready for Testing
CREATED: 2025-01-15 14:32:15 UTC

WORKFLOW COMPOSITION:
1. Webhook trigger (property leads)
2. CRM lead creation
3. Status check (approval needed?)
4. Automated or manual onboarding
5. Completion logging

INTEGRATIONS:
✓ Zoho CRM (Create/Update leads, contacts)
✓ Zoho Mail (Send welcome emails)
✓ Google Sheets (Track applications)
✓ Slack (Notify property managers)

TRIGGERS:
- Webhook: POST /webhook/property-lead
- Manual: Via dashboard button
- Schedule: Daily summary report (optional)

ESTIMATED EXECUTION TIME: 2-5 minutes per lead
SUCCESS RATE TARGET: 99.5% (6 sigma)
ERROR HANDLING: Retry 3x with exponential backoff

NEXT STEPS:

1. Review workflow details:
   /automation:workflow-details lead-to-tenant

2. Test with sample data:
   /automation:test-workflow lead-to-tenant --dry-run

3. Set up monitoring:
   /automation:monitor lead-to-tenant

4. Activate when ready:
   /automation:activate lead-to-tenant

═══════════════════════════════════════════════════════════
```

## Property Management Workflow Examples

### Example 1: Lead-to-Tenant Complete Flow

```
Trigger: Property Lead Form Submission
  ↓
Create CRM Lead
  ↓
Check Approval Status
  ├→ Pre-Approved: Auto-onboard
  └→ Needs Review: Route to manager
  ↓
Create Tenant Portal Account
  ↓
Generate Lease Documents
  ↓
Schedule Property Walk-Through
  ↓
Send Confirmation Emails
  ↓
Log in CRM + Create Activity
```

### Example 2: Maintenance Request Workflow

```
Trigger: Mobile App Maintenance Request
  ↓
Create CRM Ticket
  ↓
Extract Work Category
  ├→ Urgent (plumbing, electrical): Immediate assignment
  ├→ Standard (repairs, cleaning): Queue for next available
  └→ Preventive: Schedule within 30 days
  ↓
Assign to Contractor
  ↓
Send Work Order + Photos
  ↓
Send Tenant Confirmation
  ↓
Track Progress (via mobile updates)
  ↓
Collect Completion Photo
  ↓
Update CRM + Generate Invoice
  ↓
Send Tenant Follow-up
```

### Example 3: Rent Collection Automation

```
Trigger: Monthly rent due date
  ↓
Generate Invoice
  ↓
Send Payment Reminder (Email + SMS)
  ↓
Wait 3 days
  ↓
Check Payment Status
  ├→ Received: Update CRM, send receipt
  └→ Pending: Send late notice, escalate
  ↓
Generate Accounting Report
  ↓
Sync to Accounting System
```

---

**Uses**: n8n-mcp, workflow-automation-engine
**Model**: Haiku (fast workflow creation)
**Execution Time**: 5-10 minutes to set up basic workflow
**Complexity**: Low-Medium (template-based) to High (custom logic)
