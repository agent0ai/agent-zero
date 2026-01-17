# Customer Lifecycle + Gmail API Integration Examples

This document shows how to integrate Gmail API (Phase 2/3) features with the Customer Lifecycle tool for advanced email automation.

---

## Multi-Account Email for Different Stages

### Use Case: Department-Specific Email Accounts

**Scenario:** Use different email accounts for different customer lifecycle stages:
- `sales@company.com` - Initial contact and proposals
- `support@company.com` - Onboarding and ongoing support
- `success@company.com` - Customer success and renewals

### Implementation Example

```python
# 1. Authenticate all department accounts
{
  "tool": "email_advanced",
  "args": {
    "action": "authenticate",
    "account_name": "sales"
  }
}

{
  "tool": "email_advanced",
  "args": {
    "action": "authenticate",
    "account_name": "support"
  }
}

{
  "tool": "email_advanced",
  "args": {
    "action": "authenticate",
    "account_name": "success"
  }
}

# 2. Capture lead and send welcome from sales@
{
  "tool": "customer_lifecycle",
  "args": {
    "action": "capture_lead",
    "name": "John Smith",
    "company": "Acme Corp",
    "email": "john@acme.com",
    "industry": "Technology",
    "initial_inquiry": "Need cloud migration solution"
  }
}

# 3. Send welcome email from sales@ with label
{
  "tool": "email_advanced",
  "args": {
    "action": "send_gmail",
    "account_name": "sales",
    "to": "john@acme.com",
    "subject": "Welcome to Our Platform - Let's Discuss Your Cloud Migration",
    "body": "Hi John,\n\nThank you for your interest in our cloud migration solutions...",
    "labels": ["lead", "cloud-migration", "Q1-2026"]
  }
}

# 4. Generate proposal and send from sales@ with proposal label
{
  "tool": "customer_lifecycle",
  "args": {
    "action": "generate_proposal",
    "customer_id": "C001",
    "scope": "Cloud migration for 50 VMs",
    "timeline": "3 months",
    "pricing": "$150,000"
  }
}

# 5. Send proposal as draft for manager review
{
  "tool": "email_advanced",
  "args": {
    "action": "create_draft",
    "account_name": "sales",
    "to": "john@acme.com",
    "subject": "Cloud Migration Proposal - Acme Corp",
    "body": "Please find attached our comprehensive cloud migration proposal...",
    "labels": ["proposal", "high-value", "Q1-2026"],
    "attachments": ["/path/to/proposal_C001.pdf"]
  }
}

# 6. After customer accepts, move to support@ for onboarding
{
  "tool": "email_advanced",
  "args": {
    "action": "send_gmail",
    "account_name": "support",
    "to": "john@acme.com",
    "subject": "Welcome to Onboarding - Your Dedicated Support Team",
    "body": "Congratulations on choosing our platform! Your onboarding specialist will...",
    "labels": ["onboarding", "new-customer", "acme-corp"]
  }
}

# 7. Enable push notifications for support@ to catch customer questions
{
  "tool": "email_advanced",
  "args": {
    "action": "enable_push",
    "account_name": "support",
    "project_id": "company-support",
    "topic_name": "customer-support-emails"
  }
}
```

**Benefits:**
- 6,000 emails/day capacity (3 accounts × 2,000)
- Department-specific organization
- Email context preserved per stage
- Manager review via drafts
- Instant support response with push

---

## Label-Based Pipeline Organization

### Use Case: Organize Customer Pipeline with Gmail Labels

**Scenario:** Use Gmail labels to organize customer emails by stage, priority, and industry.

### Implementation Example

```python
# 1. Create labels for customer stages
{
  "tool": "email_advanced",
  "args": {
    "action": "create_label",
    "account_name": "sales",
    "label_name": "pipeline/lead"
  }
}

{
  "tool": "email_advanced",
  "args": {
    "action": "create_label",
    "account_name": "sales",
    "label_name": "pipeline/qualified"
  }
}

{
  "tool": "email_advanced",
  "args": {
    "action": "create_label",
    "account_name": "sales",
    "label_name": "pipeline/proposal-sent"
  }
}

{
  "tool": "email_advanced",
  "args": {
    "action": "create_label",
    "account_name": "sales",
    "label_name": "pipeline/customer"
  }
}

# 2. Create labels for industries
{
  "tool": "email_advanced",
  "args": {
    "action": "create_label",
    "account_name": "sales",
    "label_name": "industry/technology"
  }
}

{
  "tool": "email_advanced",
  "args": {
    "action": "create_label",
    "account_name": "sales",
    "label_name": "industry/finance"
  }
}

# 3. Create labels for priority
{
  "tool": "email_advanced",
  "args": {
    "action": "create_label",
    "account_name": "sales",
    "label_name": "priority/high-value"
  }
}

# 4. When capturing lead, apply appropriate labels
{
  "tool": "customer_lifecycle",
  "args": {
    "action": "capture_lead",
    "name": "Sarah Johnson",
    "company": "FinTech Inc",
    "email": "sarah@fintech.com",
    "industry": "Finance"
  }
}

# 5. Send email and apply multiple labels
{
  "tool": "email_advanced",
  "args": {
    "action": "send_gmail",
    "account_name": "sales",
    "to": "sarah@fintech.com",
    "subject": "Financial Services Cloud Solutions",
    "body": "Hi Sarah, we specialize in secure cloud solutions for financial services...",
    "labels": ["pipeline/lead", "industry/finance", "Q1-2026"]
  }
}

# 6. After proposal sent, update labels
{
  "tool": "email_advanced",
  "args": {
    "action": "search_advanced",
    "account_name": "sales",
    "sender": "sarah@fintech.com",
    "label": "pipeline/lead"
  }
}

# 7. Apply new labels to move through pipeline
{
  "tool": "email_advanced",
  "args": {
    "action": "apply_labels",
    "account_name": "sales",
    "message_ids": ["msg_id_from_search"],
    "labels_to_add": ["pipeline/proposal-sent", "priority/high-value"],
    "labels_to_remove": ["pipeline/lead"]
  }
}

# 8. Search for all high-value proposals
{
  "tool": "email_advanced",
  "args": {
    "action": "search_advanced",
    "account_name": "sales",
    "label": "priority/high-value",
    "after": "2026/01/01"
  }
}
```

**Benefits:**
- Visual pipeline organization in Gmail
- Nested labels (pipeline/, industry/, priority/)
- Batch label operations for efficiency
- Advanced search by multiple criteria
- Easy filtering for reports

---

## Proposal Review Workflow with Drafts

### Use Case: Manager Approval Before Sending Proposals

**Scenario:** Sales reps create proposal drafts that managers review and approve before sending to customers.

### Implementation Example

```python
# 1. Sales rep generates proposal
{
  "tool": "customer_lifecycle",
  "args": {
    "action": "generate_proposal",
    "customer_id": "C123",
    "scope": "Enterprise cloud migration with 24/7 support",
    "timeline": "6 months",
    "pricing": "$500,000"
  }
}

# 2. Create draft for manager review
{
  "tool": "email_advanced",
  "args": {
    "action": "create_draft",
    "account_name": "sales",
    "to": "cto@enterprise.com",
    "subject": "Enterprise Cloud Migration Proposal - $500K",
    "body": "Dear CTO,\n\nPlease find attached our comprehensive proposal...\n\n[Agent will insert proposal details]",
    "labels": ["proposal", "enterprise", "needs-review"],
    "attachments": ["/path/to/enterprise_proposal_C123.pdf"]
  }
}

# Response includes draft_id for tracking

# 3. Manager reviews in Gmail UI (native interface)
# - Edits subject/body if needed
# - Checks attachment
# - Verifies pricing and terms

# 4. After approval, send draft via API
{
  "tool": "email_advanced",
  "args": {
    "action": "send_draft",
    "account_name": "sales",
    "draft_id": "draft_xyz123"
  }
}

# 5. Track proposal status
{
  "tool": "customer_lifecycle",
  "args": {
    "action": "track_proposal",
    "customer_id": "C123",
    "status": "sent",
    "sent_date": "2026-01-14",
    "notes": "Manager approved, sent to CTO"
  }
}

# 6. Apply labels to mark as sent
{
  "tool": "email_advanced",
  "args": {
    "action": "search_advanced",
    "account_name": "sales",
    "subject": "Enterprise Cloud Migration Proposal",
    "after": "2026/01/14"
  }
}

{
  "tool": "email_advanced",
  "args": {
    "action": "apply_labels",
    "account_name": "sales",
    "message_ids": ["msg_id_from_sent"],
    "labels_to_add": ["proposal-sent", "awaiting-response"],
    "labels_to_remove": ["needs-review"]
  }
}

# 7. List all drafts needing review
{
  "tool": "email_advanced",
  "args": {
    "action": "list_drafts",
    "account_name": "sales"
  }
}

# Filter for proposals with "needs-review" label
```

**Benefits:**
- Quality control before sending
- Manager review in familiar Gmail UI
- Audit trail of draft creation and sending
- Prevents costly mistakes on high-value proposals
- Automatic label updates for tracking

---

## Real-Time Customer Response Handling

### Use Case: Instant Response to Customer Inquiries

**Scenario:** Use push notifications to respond to customer questions within seconds, creating support tickets automatically.

### Implementation Example

```python
# 1. Enable push notifications for support account
{
  "tool": "email_advanced",
  "args": {
    "action": "enable_push",
    "account_name": "support",
    "project_id": "company-support",
    "topic_name": "customer-inquiries"
  }
}

# 2. Push notification triggers when customer emails support@
# (This happens automatically via Pub/Sub webhook)

# 3. Agent receives notification and reads new email
{
  "tool": "email_advanced",
  "args": {
    "action": "read_gmail",
    "account_name": "support",
    "query": "is:unread from:john@acme.com",
    "max_results": 1
  }
}

# 4. Check customer status
{
  "tool": "customer_lifecycle",
  "args": {
    "action": "get_customer_view",
    "customer_email": "john@acme.com"
  }
}

# 5. Send auto-reply (< 2 seconds from customer email)
{
  "tool": "email_advanced",
  "args": {
    "action": "send_gmail",
    "account_name": "support",
    "to": "john@acme.com",
    "subject": "Re: Technical Question - Support Ticket Created",
    "body": "Hi John,\n\nThank you for reaching out! We've received your question and created support ticket #1234.\n\nOur team will respond within 2 hours.\n\nBest regards,\nSupport Team",
    "labels": ["auto-reply", "ticket-created"],
    "thread_id": "thread_from_original_email"
  }
}

# 6. Create internal support ticket (custom tool or database)
# (Not shown - depends on your ticketing system)

# 7. Apply labels for tracking
{
  "tool": "email_advanced",
  "args": {
    "action": "apply_labels",
    "account_name": "support",
    "message_ids": ["original_email_id"],
    "labels_to_add": ["ticket-1234", "customer/acme-corp", "status/in-progress"]
  }
}

# 8. Check customer health for context
{
  "tool": "customer_lifecycle",
  "args": {
    "action": "check_customer_health",
    "customer_id": "C001"
  }
}

# If customer health is low, escalate immediately
{
  "tool": "email_advanced",
  "args": {
    "action": "send_gmail",
    "account_name": "support",
    "to": "manager@company.com",
    "subject": "URGENT: At-Risk Customer - Acme Corp",
    "body": "Customer health score low (45%). Immediate attention required.\n\nTicket #1234 created.",
    "labels": ["escalation", "urgent"]
  }
}
```

**Benefits:**
- <2 second response time (vs 5-15 min polling)
- Automatic ticket creation
- Customer context for personalized response
- Escalation based on customer health
- Thread tracking for conversation continuity

---

## Automated Follow-Up Sequences

### Use Case: Multi-Touch Follow-Up After Proposal

**Scenario:** Automatically send follow-up emails at intervals after proposal sent, tracking responses.

### Implementation Example

```python
# 1. Send initial proposal
{
  "tool": "customer_lifecycle",
  "args": {
    "action": "generate_proposal",
    "customer_id": "C456",
    "scope": "Cloud migration + DevOps automation",
    "timeline": "4 months",
    "pricing": "$250,000"
  }
}

{
  "tool": "email_advanced",
  "args": {
    "action": "send_gmail",
    "account_name": "sales",
    "to": "prospect@company.com",
    "subject": "Cloud Migration Proposal - DevOps Automation Included",
    "body": "...",
    "labels": ["proposal", "follow-up-day-3"],
    "attachments": ["/path/to/proposal_C456.pdf"]
  }
}

# Save thread_id for follow-ups
# thread_id: "thread_abc123"

# 2. Day 3 Follow-Up (automated via scheduled task)
{
  "tool": "email_advanced",
  "args": {
    "action": "search_advanced",
    "account_name": "sales",
    "sender": "prospect@company.com",
    "after": "2026/01/11",
    "label": "proposal"
  }
}

# If no response, send follow-up
{
  "tool": "email_advanced",
  "args": {
    "action": "send_gmail",
    "account_name": "sales",
    "to": "prospect@company.com",
    "subject": "Re: Cloud Migration Proposal - Any Questions?",
    "body": "Hi,\n\nI wanted to follow up on the proposal I sent last week...",
    "labels": ["follow-up-1", "follow-up-day-7"],
    "thread_id": "thread_abc123"
  }
}

# 3. Day 7 Follow-Up
{
  "tool": "email_advanced",
  "args": {
    "action": "send_gmail",
    "account_name": "sales",
    "to": "prospect@company.com",
    "subject": "Re: Cloud Migration Proposal - Special Offer Expiring",
    "body": "Quick note - our Q1 pricing is available until Jan 31...",
    "labels": ["follow-up-2", "follow-up-day-14"],
    "thread_id": "thread_abc123"
  }
}

# 4. If customer responds, remove follow-up labels
{
  "tool": "email_advanced",
  "args": {
    "action": "apply_labels",
    "account_name": "sales",
    "message_ids": ["response_msg_id"],
    "labels_to_add": ["customer-responded", "needs-call"],
    "labels_to_remove": ["follow-up-day-14"]
  }
}

# 5. Update customer lifecycle
{
  "tool": "customer_lifecycle",
  "args": {
    "action": "track_proposal",
    "customer_id": "C456",
    "status": "customer_responded",
    "response_date": "2026-01-18",
    "notes": "Customer interested, requested call"
  }
}
```

**Benefits:**
- Automated multi-touch sequences
- Thread continuity in Gmail
- Response tracking with labels
- Scheduled follow-ups based on labels
- Stop follow-ups when customer responds

---

## Best Practices

### 1. Label Naming Convention
```
pipeline/lead
pipeline/qualified
pipeline/proposal-sent
pipeline/customer

industry/technology
industry/finance
industry/healthcare

priority/high-value
priority/enterprise
priority/urgent

status/needs-review
status/in-progress
status/completed
```

### 2. Account Assignment
- **sales@** - Leads, proposals, initial contact
- **support@** - Onboarding, tickets, ongoing support
- **success@** - Renewals, upsells, health monitoring
- **dev@** - Technical discussions, API support

### 3. Draft Workflow
1. Sales rep creates draft with "needs-review" label
2. Manager reviews in Gmail UI
3. Manager edits if needed or sends via API
4. Apply "sent" label and remove "needs-review"

### 4. Push Notification Strategy
- Enable push for support@ (instant ticket creation)
- Enable push for sales@ if monitoring high-value accounts
- Set up callbacks for automated workflows
- Use history tracking for missed events during downtime

### 5. Search Optimization
```python
# Find all unanswered high-value proposals
{
  "action": "search_advanced",
  "label": "priority/high-value",
  "is_unread": false,
  "after": "2026/01/01",
  "has_attachment": true
}

# Find all customers needing follow-up
{
  "action": "search_advanced",
  "label": "follow-up-day-3",
  "after": "2026/01/11"
}

# Find all tickets from specific customer
{
  "action": "search_advanced",
  "sender": "customer@company.com",
  "label": "ticket"
}
```

---

## Integration Checklist

- [ ] Authenticate all department accounts (sales, support, success)
- [ ] Create label hierarchy for pipeline, industry, priority
- [ ] Enable push notifications for support account
- [ ] Set up draft review workflow
- [ ] Configure follow-up automation with labels
- [ ] Test thread continuity for conversations
- [ ] Set up customer health monitoring with email integration
- [ ] Create dashboards for proposal tracking
- [ ] Document account usage and quotas (2,000/day per account)
- [ ] Train team on Gmail UI for draft reviews

---

## Summary

By integrating Gmail API (Phase 2/3) with Customer Lifecycle:

**Achieved:**
- ✅ Multi-department email organization (6,000 emails/day capacity)
- ✅ Visual pipeline tracking with labels
- ✅ Manager approval workflow with drafts
- ✅ <2 second response time with push notifications
- ✅ Automated follow-up sequences with thread tracking
- ✅ Customer context for personalized communication

**Next Steps:**
1. Follow examples to set up multi-account authentication
2. Create label structure for your pipeline
3. Enable push notifications for support
4. Test draft workflow with sales team
5. Implement follow-up automation

**Documentation:**
- Main guide: `docs/GMAIL_API_PHASE2_PHASE3.md`
- Quick start: `docs/EMAIL_QUICK_START.md`
- Phase 1 basics: `docs/EMAIL_INTEGRATION_PHASE1.md`
