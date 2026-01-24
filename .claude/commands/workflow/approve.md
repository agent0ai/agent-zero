---
description: Approve pending operations (Zoho data modifications, deployments, etc.)
argument-hint: [pending-id or 'list']
model: claude-3-5-haiku-20241022
allowed-tools: AskUserQuestion, Read, Write
---

Manage and approve pending operations that require human authorization.

## What This Command Does

This command provides a centralized approval workflow for operations that require human review before execution:

- **Zoho CRM Operations**: Lead creation, contact updates, deal modifications
- **Communication Operations**: Email campaigns, SMS blasts, bulk notifications
- **Deployment Operations**: Production deployments, database migrations
- **Data Sync Operations**: Multi-system data synchronization
- **Configuration Changes**: Environment variable updates, API key rotations

All pending operations are queued in an approval workflow and require explicit human authorization before executing.

## Task to Process

**Pending ID**: $ARGUMENTS (or "list" to see all pending operations)

## Step 1: Load Pending Operations

Check for pending approval requests in the workflow queue:

```bash
# Pending operations are stored in:
/home/webemo-aaron/projects/prompt-blueprint/.workflow/pending/
```

If $ARGUMENTS is "list" or empty:

- List all pending operations with IDs, types, timestamps
- Show summary statistics (total pending, by type, by priority)

If $ARGUMENTS contains a specific ID:

- Load the specific pending operation details
- Display full operation preview

## Step 2: Display Operation Details

For each pending operation, show:

```
═══════════════════════════════════════════════════
           PENDING OPERATION APPROVAL
═══════════════════════════════════════════════════

OPERATION ID: [unique-id]
TYPE: [Zoho CRM Lead / Email Campaign / Deployment / etc.]
CREATED: [timestamp]
PRIORITY: [Low / Medium / High / Critical]
REQUESTED BY: [user/agent]
STATUS: Pending Approval

OPERATION DETAILS:
[Detailed breakdown of what will be executed]

AFFECTED SYSTEMS:
- [System 1]: [Impact description]
- [System 2]: [Impact description]

DATA PREVIEW:
[Show data that will be created/modified]

RISK ASSESSMENT:
- Impact: [Low / Medium / High]
- Reversible: [Yes / No]
- Compliance: [Affected regulations if any]

ESTIMATED EXECUTION TIME: [duration]

═══════════════════════════════════════════════════
```

## Step 3: Risk Analysis

Automatically analyze the operation for:

1. **Data Quality Checks**:
   - Required fields present
   - Valid data formats
   - No obvious errors
   - Duplicate detection (for CRM)

2. **Compliance Validation**:
   - HIPAA compliance (if healthcare data)
   - PCI-DSS compliance (if payment data)
   - Email regulations (CAN-SPAM, GDPR)
   - SMS regulations (TCPA)

3. **System Impact**:
   - Affected records count
   - API rate limits
   - Quota consumption
   - Dependencies and side effects

4. **Security Considerations**:
   - Sensitive data exposure
   - Permission levels required
   - Audit trail completeness

Display results:

```
RISK ANALYSIS:
✓ Data quality: PASSED
✓ Compliance: PASSED (HIPAA, CAN-SPAM)
⚠ System impact: MODERATE (47 records affected)
✓ Security: PASSED

RECOMMENDATIONS:
- Review recipient list for opt-out status
- Consider staging environment test first
- Schedule during low-traffic hours
```

## Step 4: Request Approval Decision

Use **AskUserQuestion** to collect approval decision:

**Question**: "What action would you like to take on this pending operation?"

**Options**:

1. **"Approve & Execute"** - Proceed with operation immediately
   - Description: Execute the operation now with full audit logging

2. **"Approve & Schedule"** - Approve but schedule for later
   - Description: Set a specific date/time for automatic execution

3. **"Request Changes"** - Require modifications before approval
   - Description: Send back to requester with change requests

4. **"Reject & Cancel"** - Permanently reject this operation
   - Description: Cancel operation and log rejection reason

## Step 5: Execute Based on Decision

### If "Approve & Execute"

1. **Pre-Execution Checks**:

   ```
   Running pre-flight checks...
   ✓ API credentials valid
   ✓ System connectivity OK
   ✓ Rate limits available
   ✓ All dependencies ready
   ```

2. **Execute Operation**:
   - For Zoho operations: Call appropriate Zoho API
   - For deployments: Trigger deployment pipeline
   - For data sync: Execute synchronization
   - Log all actions with timestamps

3. **Post-Execution Validation**:

   ```
   ✓ Operation completed successfully
   ✓ Data integrity verified
   ✓ Audit trail recorded
   ✓ Notifications sent
   ```

4. **Display Results**:

   ```
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   ✓ OPERATION COMPLETED SUCCESSFULLY
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

   Operation ID: PENDING-12345
   Execution Time: 2.4 seconds
   Records Processed: 47
   Status: SUCCESS

   DETAILS:
   - Created: 12 records
   - Updated: 35 records
   - Skipped: 0 records
   - Failed: 0 records

   NEXT STEPS:
   - Monitor system for 24 hours
   - Review success metrics
   - Check for any anomalies

   AUDIT LOG: /workflow/logs/PENDING-12345-completed.json
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   ```

### If "Approve & Schedule"

1. Use **AskUserQuestion** to collect scheduling details:
   - Execution date/time
   - Timezone
   - Recurring schedule (if applicable)
   - Notification preferences

2. Save scheduled operation:

   ```
   ✓ Operation scheduled successfully

   Scheduled Execution: 2025-12-01 09:00:00 EST
   Recurrence: None (one-time)
   Reminder: 30 minutes before

   You can modify or cancel this scheduled operation using:
   /workflow/approve PENDING-12345 --cancel-schedule
   ```

### If "Request Changes"

1. Use **AskUserQuestion** to collect change requests:
   - What needs to be modified?
   - Specific concerns or issues?
   - Additional requirements?

2. Send back to requester:

   ```
   ✓ Change request submitted

   Operation: PENDING-12345
   Status: Changes Requested
   Assigned To: [original requester]

   REQUESTED CHANGES:
   - [List of required changes]

   The requester will be notified and can resubmit after making changes.
   ```

### If "Reject & Cancel"

1. Use **AskUserQuestion** to collect rejection reason:
   - Why is this being rejected?
   - What policy/rule does it violate?
   - Alternative actions to suggest?

2. Record rejection:

   ```
   ✓ Operation rejected and cancelled

   Operation ID: PENDING-12345
   Status: REJECTED
   Rejected By: [user]
   Reason: [rejection reason]

   AUDIT LOG:
   - Rejection recorded
   - Requester notified
   - Resources released

   This decision has been logged for compliance purposes.
   ```

## Step 6: Update Workflow State

1. Move operation from `/pending/` to appropriate folder:
   - `/completed/` for approved & executed
   - `/scheduled/` for approved & scheduled
   - `/rejected/` for rejected
   - `/revision/` for change requests

2. Update operation metadata:

   ```json
   {
     "operation_id": "PENDING-12345",
     "status": "completed",
     "approved_by": "user@example.com",
     "approved_at": "2025-11-25T10:30:00Z",
     "executed_at": "2025-11-25T10:30:15Z",
     "execution_time_seconds": 2.4,
     "records_affected": 47,
     "audit_trail": [...]
   }
   ```

3. Send notifications:
   - Email to requester with status
   - Slack/Teams notification (if configured)
   - Update dashboard metrics

## Business Value & ROI

### Risk Mitigation

- **Prevented errors**: Human review catches mistakes before execution
- **Compliance assurance**: Ensures regulatory requirements are met
- **Audit trail**: Complete record for compliance and forensics

### Operational Efficiency

- **Centralized approvals**: Single place to review all pending operations
- **Batch processing**: Approve multiple operations efficiently
- **Automated validation**: Pre-execution checks catch issues early

### Cost Savings

- **Reduced rework**: Catch errors before they impact systems
- **API efficiency**: Batch operations reduce API calls
- **Time savings**: 5-10 minutes per approval vs. manual process

### Measurable Impact

- **Approval velocity**: Average time from request to approval
- **Error prevention**: Number of issues caught during review
- **Compliance rate**: 100% audit trail for all operations

## Success Metrics

Track these KPIs to measure workflow effectiveness:

```
APPROVAL WORKFLOW METRICS (Last 30 Days)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Total Operations: 156
- Approved: 142 (91%)
- Rejected: 8 (5%)
- Pending: 6 (4%)

Average Approval Time: 12 minutes
Average Execution Time: 3.2 seconds

By Type:
- Zoho CRM: 89 operations (94% approval)
- Email Campaigns: 34 operations (88% approval)
- Deployments: 21 operations (95% approval)
- Data Sync: 12 operations (92% approval)

Risk Catches:
- Data quality issues: 5
- Compliance violations: 2
- Duplicate prevention: 11

ROI:
- Errors prevented: 18
- Time saved: 26 hours
- Cost avoided: $4,200
```

## Quality Checklist

Before approving any operation:

- [ ] All required fields are present and valid
- [ ] Compliance requirements are met
- [ ] Risk assessment completed
- [ ] Impact is understood and acceptable
- [ ] Reversibility options are clear
- [ ] Audit trail is complete
- [ ] Notifications are configured

## Error Handling

If execution fails after approval:

1. **Immediate Actions**:
   - Stop execution
   - Log error details
   - Notify approver and requester
   - Preserve system state

2. **Error Analysis**:
   - Identify root cause
   - Determine impact scope
   - Assess data integrity

3. **Recovery Options**:

   ```
   EXECUTION FAILED - RECOVERY OPTIONS

   Error: API rate limit exceeded
   Affected: 12 of 47 records processed

   OPTIONS:
   1. Retry remaining records (auto-resume)
   2. Rollback all changes
   3. Manual intervention required
   4. Cancel operation

   What would you like to do?
   ```

## Notes

- **Security**: All approvals are logged with user identity and timestamp
- **Compliance**: Maintains complete audit trail for regulatory requirements
- **Performance**: Approval checks run in <2 seconds for typical operations
- **Scalability**: Handles 1000+ pending operations efficiently
- **Integration**: Works with all Zoho, deployment, and data sync operations

## Example Usage

```bash
# List all pending operations
/workflow:approve list

# Review specific operation
/workflow:approve PENDING-12345

# Quick approve with operation ID
/workflow:approve PENDING-12345

# Interactive approval (no arguments)
/workflow:approve
# Will prompt to select from pending operations
```

## Related Commands

- `/workflow:collect-data` - Create operations that require approval
- `/workflow:orchestrate` - Multi-step workflows with approval gates
- `/workflow:visualize` - See approval workflow status
- `/zoho:create-lead` - Creates operations requiring approval
- `/zoho:send-email` - Creates email operations requiring approval
