# Virtual Team + Gmail API Integration Examples

This document shows how to integrate Gmail API (Phase 2/3) features with the Virtual Team tool for advanced team notification and collaboration.

---

## Multi-Account Team Notifications

### Use Case: Department-Specific Team Communications

**Scenario:** Use different email accounts for different team functions:
- `team@company.com` - General team updates and digests
- `dev@company.com` - Development team notifications
- `projects@company.com` - Project-specific communications

### Implementation Example

```python
# 1. Authenticate all team accounts
{
  "tool": "email_advanced",
  "args": {
    "action": "authenticate",
    "account_name": "team"
  }
}

{
  "tool": "email_advanced",
  "args": {
    "action": "authenticate",
    "account_name": "dev"
  }
}

{
  "tool": "email_advanced",
  "args": {
    "action": "authenticate",
    "account_name": "projects"
  }
}

# 2. Create task and notify developer from dev@
{
  "tool": "virtual_team",
  "args": {
    "action": "create_task",
    "title": "Implement OAuth2 for New API",
    "description": "Add OAuth2 authentication to customer API endpoints",
    "priority": "high",
    "assignee": "developer@company.com",
    "due_date": "2026-01-21",
    "tags": ["backend", "security", "api"]
  }
}

# 3. Send task notification from dev@ with labels
{
  "tool": "email_advanced",
  "args": {
    "action": "send_gmail",
    "account_name": "dev",
    "to": "developer@company.com",
    "subject": "🔴 High Priority Task Assigned: Implement OAuth2 for New API",
    "body": "**Task:** Implement OAuth2 for New API\n**Priority:** High\n**Due Date:** 2026-01-21\n\n**Description:**\nAdd OAuth2 authentication to customer API endpoints...\n\n**Tags:** backend, security, api",
    "labels": ["task-assignment", "priority-high", "team-dev"]
  }
}

# 4. Send daily digest from team@ for all members
{
  "tool": "virtual_team",
  "args": {
    "action": "get_team_summary"
  }
}

{
  "tool": "email_advanced",
  "args": {
    "action": "send_gmail",
    "account_name": "team",
    "to": ["dev1@company.com", "dev2@company.com", "manager@company.com"],
    "subject": "Daily Team Digest - Jan 14, 2026",
    "body": "**Team Summary**\n\n✅ Completed: 8 tasks\n🔄 In Progress: 12 tasks\n📋 Total Active: 35 tasks\n\n**Top Priorities:**\n1. OAuth2 implementation (due Jan 21)\n2. Performance optimization (due Jan 18)...",
    "labels": ["digest", "daily", "team-wide"]
  }
}

# 5. Project update from projects@
{
  "tool": "email_advanced",
  "args": {
    "action": "send_gmail",
    "account_name": "projects",
    "to": "client@customer.com",
    "subject": "Weekly Project Update - Cloud Migration Phase 2",
    "body": "**Project Status Update**\n\nPhase 2 of your cloud migration is 75% complete...",
    "labels": ["project-update", "client-acme", "weekly"]
  }
}
```

**Benefits:**
- 6,000 emails/day capacity (3 accounts × 2,000)
- Department-specific email context
- Organized by function (team/dev/projects)
- Easy filtering by account in Gmail
- Professional separation of concerns

---

## Label-Based Task Organization

### Use Case: Organize Team Communications with Gmail Labels

**Scenario:** Use Gmail labels to organize task assignments, project updates, and team communications by priority, team, and status.

### Implementation Example

```python
# 1. Create labels for task priorities
{
  "tool": "email_advanced",
  "args": {
    "action": "create_label",
    "account_name": "team",
    "label_name": "tasks/critical"
  }
}

{
  "tool": "email_advanced",
  "args": {
    "action": "create_label",
    "account_name": "team",
    "label_name": "tasks/high"
  }
}

{
  "tool": "email_advanced",
  "args": {
    "action": "create_label",
    "account_name": "team",
    "label_name": "tasks/medium"
  }
}

# 2. Create labels for teams
{
  "tool": "email_advanced",
  "args": {
    "action": "create_label",
    "account_name": "team",
    "label_name": "team/backend"
  }
}

{
  "tool": "email_advanced",
  "args": {
    "action": "create_label",
    "account_name": "team",
    "label_name": "team/frontend"
  }
}

{
  "tool": "email_advanced",
  "args": {
    "action": "create_label",
    "account_name": "team",
    "label_name": "team/devops"
  }
}

# 3. Create labels for status
{
  "tool": "email_advanced",
  "args": {
    "action": "create_label",
    "account_name": "team",
    "label_name": "status/assigned"
  }
}

{
  "tool": "email_advanced",
  "args": {
    "action": "create_label",
    "account_name": "team",
    "label_name": "status/in-progress"
  }
}

{
  "tool": "email_advanced",
  "args": {
    "action": "create_label",
    "account_name": "team",
    "label_name": "status/completed"
  }
}

# 4. Assign task with appropriate labels
{
  "tool": "virtual_team",
  "args": {
    "action": "create_task",
    "title": "Fix Critical Database Performance Issue",
    "priority": "critical",
    "assignee": "backend-dev@company.com",
    "tags": ["database", "performance", "urgent"]
  }
}

{
  "tool": "email_advanced",
  "args": {
    "action": "send_gmail",
    "account_name": "team",
    "to": "backend-dev@company.com",
    "subject": "🚨 CRITICAL: Fix Database Performance Issue",
    "body": "**CRITICAL TASK**\n\nDatabase queries timing out...",
    "labels": ["tasks/critical", "team/backend", "status/assigned"]
  }
}

# 5. When task starts, update labels
{
  "tool": "email_advanced",
  "args": {
    "action": "search_advanced",
    "account_name": "team",
    "subject": "Fix Critical Database Performance Issue",
    "label": "status/assigned"
  }
}

{
  "tool": "email_advanced",
  "args": {
    "action": "apply_labels",
    "account_name": "team",
    "message_ids": ["task_email_id"],
    "labels_to_add": ["status/in-progress"],
    "labels_to_remove": ["status/assigned"]
  }
}

# 6. Search for all critical backend tasks
{
  "tool": "email_advanced",
  "args": {
    "action": "search_advanced",
    "account_name": "team",
    "label": "tasks/critical AND team/backend"
  }
}

# 7. List all labels to see organization
{
  "tool": "email_advanced",
  "args": {
    "action": "list_labels",
    "account_name": "team"
  }
}
```

**Benefits:**
- Visual task organization in Gmail
- Nested labels (tasks/, team/, status/)
- Multi-dimensional filtering (priority + team + status)
- Easy dashboard creation with Gmail filters
- Quick search for specific task categories

---

## Draft Review for Team Communications

### Use Case: Manager Approval for Client Communications

**Scenario:** Team members create draft emails to clients that managers review before sending.

### Implementation Example

```python
# 1. Team member creates project update draft
{
  "tool": "virtual_team",
  "args": {
    "action": "get_project_summary",
    "project_id": "P123"
  }
}

# 2. Create draft for manager review
{
  "tool": "email_advanced",
  "args": {
    "action": "create_draft",
    "account_name": "projects",
    "to": "client@enterprise.com",
    "subject": "Project Status Update - Week of Jan 14",
    "body": "Dear Client,\n\nI'm pleased to share this week's progress on your project:\n\n**Completed This Week:**\n- Database migration (Phase 1)\n- API integration testing\n- Security audit completed\n\n**Next Week:**\n- Frontend deployment\n- User acceptance testing\n\n**Timeline:** On track for Jan 31 delivery\n\nPlease let me know if you have any questions.",
    "labels": ["project-update", "needs-review", "client-enterprise"]
  }
}

# Draft created with draft_id for tracking

# 3. Notify manager that draft needs review
{
  "tool": "email_advanced",
  "args": {
    "action": "send_gmail",
    "account_name": "team",
    "to": "manager@company.com",
    "subject": "Draft Ready for Review - Enterprise Client Update",
    "body": "A project update draft is ready for your review in projects@company.com.\n\nClient: Enterprise Corp\nProject: Cloud Migration\nDraft ID: draft_xyz123",
    "labels": ["draft-notification", "manager-action-required"]
  }
}

# 4. Manager reviews draft in Gmail UI
# - Checks accuracy of progress claims
# - Verifies timeline commitments
# - Edits tone or adds details

# 5. After approval, send draft
{
  "tool": "email_advanced",
  "args": {
    "action": "send_draft",
    "account_name": "projects",
    "draft_id": "draft_xyz123"
  }
}

# 6. Update labels to track sent
{
  "tool": "email_advanced",
  "args": {
    "action": "search_advanced",
    "account_name": "projects",
    "subject": "Project Status Update - Week of Jan 14",
    "after": "2026/01/14"
  }
}

{
  "tool": "email_advanced",
  "args": {
    "action": "apply_labels",
    "account_name": "projects",
    "message_ids": ["sent_email_id"],
    "labels_to_add": ["sent", "awaiting-response"],
    "labels_to_remove": ["needs-review"]
  }
}

# 7. List all drafts needing review
{
  "tool": "email_advanced",
  "args": {
    "action": "list_drafts",
    "account_name": "projects"
  }
}
```

**Benefits:**
- Quality control for client communications
- Manager review before sending
- Familiar Gmail UI for editing
- Audit trail of draft → review → send
- Prevents miscommunication with clients

---

## Real-Time Task Collaboration

### Use Case: Instant Notifications for Team Updates

**Scenario:** Use push notifications to notify team members instantly when tasks are assigned, updated, or completed.

### Implementation Example

```python
# 1. Enable push notifications for team account
{
  "tool": "email_advanced",
  "args": {
    "action": "enable_push",
    "account_name": "team",
    "project_id": "company-team-collab",
    "topic_name": "team-notifications"
  }
}

# 2. Assign urgent task (triggers notification workflow)
{
  "tool": "virtual_team",
  "args": {
    "action": "create_task",
    "title": "Production Incident - API Down",
    "priority": "critical",
    "assignee": "oncall-dev@company.com",
    "tags": ["production", "incident", "urgent"]
  }
}

{
  "tool": "email_advanced",
  "args": {
    "action": "send_gmail",
    "account_name": "team",
    "to": "oncall-dev@company.com",
    "subject": "🚨 URGENT: Production Incident - API Down",
    "body": "**PRODUCTION INCIDENT**\n\nAPI is currently down. Customer impact: High\n\nPlease acknowledge immediately.",
    "labels": ["incident", "urgent", "requires-ack"]
  }
}

# 3. Push notification triggers (<2 seconds)
# Developer receives instant notification
# Can read email immediately via API

{
  "tool": "email_advanced",
  "args": {
    "action": "read_gmail",
    "account_name": "team",
    "query": "is:unread label:incident",
    "max_results": 1
  }
}

# 4. Developer acknowledges via reply
# Reply triggers push notification to manager

{
  "tool": "email_advanced",
  "args": {
    "action": "search_advanced",
    "account_name": "team",
    "sender": "oncall-dev@company.com",
    "subject": "Production Incident",
    "after": "2026/01/14"
  }
}

# 5. Auto-notify manager of acknowledgment
{
  "tool": "email_advanced",
  "args": {
    "action": "send_gmail",
    "account_name": "team",
    "to": "manager@company.com",
    "subject": "Incident Acknowledged - Developer Responding",
    "body": "Production incident has been acknowledged by on-call developer.\n\nIncident: API Down\nAssigned: oncall-dev@company.com\nStatus: In Progress",
    "labels": ["incident-update", "manager-notification"]
  }
}

# 6. When resolved, update labels
{
  "tool": "email_advanced",
  "args": {
    "action": "apply_labels",
    "account_name": "team",
    "message_ids": ["incident_thread_id"],
    "labels_to_add": ["incident-resolved"],
    "labels_to_remove": ["requires-ack", "urgent"]
  }
}

# 7. Send resolution notification
{
  "tool": "email_advanced",
  "args": {
    "action": "send_gmail",
    "account_name": "team",
    "to": ["manager@company.com", "team@company.com"],
    "subject": "✅ Incident Resolved - API Restored",
    "body": "**INCIDENT RESOLVED**\n\nAPI has been restored. Root cause: Database connection timeout.\n\nResolution time: 18 minutes",
    "labels": ["incident-resolved", "postmortem-needed"],
    "thread_id": "original_incident_thread"
  }
}
```

**Benefits:**
- <2 second notification delivery
- Instant acknowledgment tracking
- Automatic escalation workflows
- Manager visibility in real-time
- Complete incident thread in Gmail

---

## Automated Team Digests with Advanced Search

### Use Case: Smart Daily/Weekly Digests Based on Labels

**Scenario:** Generate personalized team digests using advanced search to find relevant updates.

### Implementation Example

```python
# 1. Daily Backend Team Digest
{
  "tool": "email_advanced",
  "args": {
    "action": "search_advanced",
    "account_name": "team",
    "label": "team/backend",
    "after": "2026/01/13",
    "before": "2026/01/14"
  }
}

# 2. Compile digest from results
{
  "tool": "email_advanced",
  "args": {
    "action": "send_gmail",
    "account_name": "team",
    "to": "backend-team@company.com",
    "subject": "Backend Team Digest - Jan 14, 2026",
    "body": "**Daily Backend Team Update**\n\n**New Tasks (3):**\n- Database optimization\n- API rate limiting\n- Cache implementation\n\n**Completed Tasks (5):**\n- OAuth2 integration\n- Error handling improvements\n- Unit test coverage increase\n\n**In Progress (8):**\n...",
    "labels": ["digest", "team/backend", "daily"]
  }
}

# 3. Weekly High-Priority Summary
{
  "tool": "email_advanced",
  "args": {
    "action": "search_advanced",
    "account_name": "team",
    "label": "tasks/critical OR tasks/high",
    "after": "2026/01/07",
    "is_unread": false
  }
}

{
  "tool": "email_advanced",
  "args": {
    "action": "send_gmail",
    "account_name": "team",
    "to": "manager@company.com",
    "subject": "Weekly High-Priority Task Summary",
    "body": "**High-Priority Tasks This Week**\n\n**Critical (2):**\n- Production incident (resolved)\n- Database performance (in progress)\n\n**High (7):**\n...",
    "labels": ["digest", "weekly", "manager"]
  }
}

# 4. Client Update Summary
{
  "tool": "email_advanced",
  "args": {
    "action": "search_advanced",
    "account_name": "projects",
    "label": "client-acme",
    "after": "2026/01/01"
  }
}

{
  "tool": "email_advanced",
  "args": {
    "action": "send_gmail",
    "account_name": "team",
    "to": "account-manager@company.com",
    "subject": "Acme Corp - Monthly Activity Summary",
    "body": "**Acme Corp Account Summary**\n\n**Total Communications:** 23 emails\n**Project Updates Sent:** 4\n**Support Tickets:** 2 (both resolved)\n**Proposals:** 1 (pending response)\n\n**Next Steps:**\n- Follow up on proposal (due Jan 21)\n- Schedule quarterly review",
    "labels": ["digest", "monthly", "account-summary"]
  }
}

# 5. Personal Task Digest for Each Team Member
{
  "tool": "email_advanced",
  "args": {
    "action": "search_advanced",
    "account_name": "team",
    "sender": "team@company.com",
    "subject": "Task Assigned",
    "after": "2026/01/14",
    "is_unread": true
  }
}

# Send personalized digest to each team member
# (Loop through team members)
```

**Benefits:**
- Smart filtering with advanced search
- Personalized digests per team/role
- Automated daily/weekly summaries
- Historical tracking with date ranges
- Client-specific activity summaries

---

## Thread Management for Team Discussions

### Use Case: Keep Team Discussions Organized

**Scenario:** Use Gmail threads to keep all communications about a task or project in one conversation.

### Implementation Example

```python
# 1. Create initial task assignment
{
  "tool": "virtual_team",
  "args": {
    "action": "create_task",
    "title": "Design System Architecture",
    "assignee": "architect@company.com",
    "tags": ["architecture", "design", "planning"]
  }
}

{
  "tool": "email_advanced",
  "args": {
    "action": "send_gmail",
    "account_name": "team",
    "to": "architect@company.com",
    "subject": "Task: Design System Architecture",
    "body": "Please design the system architecture for the new customer portal...",
    "labels": ["task", "architecture", "team/architecture"]
  }
}

# Save thread_id from response: "thread_arch_123"

# 2. Send updates in same thread
{
  "tool": "email_advanced",
  "args": {
    "action": "send_gmail",
    "account_name": "team",
    "to": "architect@company.com",
    "subject": "Re: Task: Design System Architecture",
    "body": "Update: Requirements doc attached for reference...",
    "labels": ["task-update"],
    "thread_id": "thread_arch_123",
    "attachments": ["/path/to/requirements.pdf"]
  }
}

# 3. Team discussion continues in thread
{
  "tool": "email_advanced",
  "args": {
    "action": "send_gmail",
    "account_name": "team",
    "to": ["architect@company.com", "tech-lead@company.com"],
    "subject": "Re: Task: Design System Architecture",
    "body": "Tech lead review requested for architecture proposal...",
    "labels": ["review-requested"],
    "thread_id": "thread_arch_123"
  }
}

# 4. Read entire thread for context
{
  "tool": "email_advanced",
  "args": {
    "action": "read_gmail",
    "account_name": "team",
    "query": "rfc822msgid:thread_arch_123"
  }
}

# 5. When completed, mark thread
{
  "tool": "email_advanced",
  "args": {
    "action": "search_advanced",
    "account_name": "team",
    "subject": "Design System Architecture"
  }
}

{
  "tool": "email_advanced",
  "args": {
    "action": "apply_labels",
    "account_name": "team",
    "message_ids": ["all_messages_in_thread"],
    "labels_to_add": ["completed", "archived"]
  }
}
```

**Benefits:**
- Complete conversation history in one thread
- Easy context retrieval
- No scattered email chains
- Gmail groups all related messages
- Simplified searching (one thread ID)

---

## Best Practices

### 1. Label Hierarchy for Teams
```
tasks/critical
tasks/high
tasks/medium
tasks/low

team/backend
team/frontend
team/devops
team/qa

status/assigned
status/in-progress
status/blocked
status/completed

projects/client-a
projects/client-b
projects/internal

digest/daily
digest/weekly
digest/monthly
```

### 2. Account Assignment
- **team@** - General team communications, digests
- **dev@** - Development team notifications, technical discussions
- **projects@** - Client communications, project updates
- **oncall@** - Incident notifications, urgent alerts

### 3. Notification Priority
- **Critical:** Push notifications enabled, instant delivery
- **High:** Email within minutes, label for filtering
- **Medium:** Daily digest inclusion
- **Low:** Weekly digest only

### 4. Thread Management
- Use `thread_id` for all related communications
- Keep task discussions in one thread
- Include relevant stakeholders via CC
- Apply labels to entire thread for organization

### 5. Draft Review Process
```python
# 1. Create draft with "needs-review" label
# 2. Notify reviewer via separate email
# 3. Reviewer edits in Gmail UI
# 4. Reviewer sends via API or Gmail
# 5. Apply "sent" label, remove "needs-review"
```

### 6. Digest Automation
```python
# Daily: 9 AM - Task assignments and completions
# Weekly: Friday 5 PM - Team summary and priorities
# Monthly: 1st of month - Client activity and metrics
# Quarterly: Project milestones and retrospectives
```

---

## Integration Checklist

- [ ] Authenticate team accounts (team@, dev@, projects@)
- [ ] Create label hierarchy for tasks, teams, status
- [ ] Enable push notifications for urgent communications
- [ ] Set up draft review workflow for client emails
- [ ] Configure digest automation (daily/weekly/monthly)
- [ ] Test thread management for task discussions
- [ ] Set up incident response workflow with push
- [ ] Create templates for common notifications
- [ ] Document account usage and quotas
- [ ] Train team on Gmail UI for draft reviews and thread management

---

## Summary

By integrating Gmail API (Phase 2/3) with Virtual Team:

**Achieved:**
- ✅ Multi-account team communications (6,000 emails/day)
- ✅ Visual task organization with labels
- ✅ Manager approval workflow for client emails
- ✅ <2 second incident notifications with push
- ✅ Automated smart digests with advanced search
- ✅ Organized team discussions with thread management

**Next Steps:**
1. Authenticate team accounts following examples
2. Create label structure for your team organization
3. Enable push notifications for urgent/incident communications
4. Set up draft review workflow for client-facing emails
5. Automate digest generation using advanced search
6. Test thread management for task discussions

**Documentation:**
- Main guide: `docs/GMAIL_API_PHASE2_PHASE3.md`
- Quick start: `docs/EMAIL_QUICK_START.md`
- Customer integration: `docs/examples/CUSTOMER_LIFECYCLE_GMAIL_INTEGRATION.md`
