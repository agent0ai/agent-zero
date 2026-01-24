---
description: Email → Task automation - converts action-required emails into tasks across Trello, Notion, and Calendar
argument-hint: "[--email-id <id>] [--auto] [--dry-run]"
model: claude-3-5-sonnet-20241022
allowed-tools:
  - Bash
  - Read
  - Write
  - AskUserQuestion
---

# Email-to-Task Workflow Automation

## Overview

**HIGH VALUE WORKFLOW** - Saves 30-45 min/day

Automatically converts action-required emails into tasks across all productivity tools with AI-powered task extraction and intelligent routing.

**Part of Phase 2**: Workflow automation for productivity integration

## What This Command Does

**Trigger**: Email flagged/labeled as "Action Required" OR manual execution

**Automation**:

1. ✅ Extracts action items from email using AI
2. ✅ Creates Trello card with email context
3. ✅ Saves to Notion tasks database
4. ✅ Links back to original Gmail thread
5. ✅ Optionally creates calendar time block
6. ✅ Indexes for universal search

**Time Saved**: 30-45 min/day = **3.5-5 hours/week**

## Usage

```bash
# Manual execution on specific email
/workflow:email-to-task --email-id msg_abc123

# Process all flagged emails
/workflow:email-to-task --auto

# Preview without creating tasks (dry-run)
/workflow:email-to-task --dry-run

# Process specific label
/workflow:email-to-task --label "Action Required"

# Interactive mode (select from recent emails)
/workflow:email-to-task --interactive
```

## Automatic Trigger Setup

### Gmail Filter Auto-Label

Create Gmail filter:

- **Criteria**: Contains words like "action required", "please complete", "need you to"
- **Action**: Apply label "Action Required"
- **Then**: Workflow automatically triggered

### n8n Webhook Trigger

```bash
# Set up automatic processing every hour
# Checks for new "Action Required" emails
# Runs workflow automatically
```

## Step-by-Step Execution

### 1. Fetch Email Content

```javascript
// n8n Workflow Node 1: Gmail MCP Integration
const email = await mcp.gmail.getMessage({
  id: emailId,
  format: 'full'
});

const emailData = {
  id: email.id,
  threadId: email.threadId,
  from: email.payload.headers.find(h => h.name === 'From').value,
  to: email.payload.headers.find(h => h.name === 'To').value,
  subject: email.payload.headers.find(h => h.name === 'Subject').value,
  date: email.payload.headers.find(h => h.name === 'Date').value,
  snippet: email.snippet,
  body: extractBody(email.payload)
};
```

### 2. AI Extract Action Items

```javascript
// n8n Workflow Node 2: Claude AI Extraction
const extraction = await claude.extract({
  prompt: `Extract actionable tasks from this email:

  From: ${emailData.from}
  Subject: ${emailData.subject}
  Date: ${emailData.date}

  Email Content:
  ${emailData.body}

  Extract:
  1. Main action required (clear, actionable)
  2. Any sub-tasks or steps mentioned
  3. Deadline or due date (if mentioned)
  4. Priority level (urgent/high/medium/low)
  5. Estimated time to complete

  Return JSON:
  {
    "mainAction": "Clear action verb + specific task",
    "subTasks": ["subtask 1", "subtask 2"],
    "deadline": "2025-02-01" or null,
    "priority": "urgent|high|medium|low",
    "estimatedTime": "2 hours",
    "reasoning": "Why this is the action"
  }
  `
});
```

### 3. Create Trello Card

```javascript
// n8n Workflow Node 3: Trello MCP Integration
const trelloCard = await mcp.trello.createCard({
  name: extraction.mainAction,
  desc: `From: ${emailData.from}
Subject: ${emailData.subject}
Date: ${emailData.date}

Email Link: https://mail.google.com/mail/u/0/#inbox/${emailData.id}

---

${emailData.body}

---

AI Extracted Action:
${extraction.mainAction}

Estimated Time: ${extraction.estimatedTime}
Deadline: ${extraction.deadline || 'Not specified'}
`,
  idList: getListByPriority(extraction.priority),
  due: extraction.deadline ? new Date(extraction.deadline).toISOString() : null,
  idLabels: [getLabelId('from-email'), getLabelId(extraction.priority)],
  pos: 'top'
});

// Add checklist if subtasks exist
if (extraction.subTasks && extraction.subTasks.length > 0) {
  await mcp.trello.createChecklist({
    idCard: trelloCard.id,
    name: 'Steps',
    checkItems: extraction.subTasks.map(st => ({ name: st }))
  });
}
```

### 4. Save to Notion

```javascript
// n8n Workflow Node 4: Notion MCP Integration
const notionTask = await mcp.notion.createPage({
  parent: {
    database_id: context.integrations.notion.database_ids.tasks
  },
  properties: {
    Name: { title: [{ text: { content: extraction.mainAction } }] },
    Status: { select: { name: 'To Do' } },
    Priority: { select: { name: extraction.priority } },
    Due: extraction.deadline ? { date: { start: extraction.deadline } } : null,
    Source: { select: { name: 'Email' } },
    'Email From': { email: extractEmail(emailData.from) },
    'Email Subject': { rich_text: [{ text: { content: emailData.subject } }] },
    'Trello Card': { url: trelloCard.shortUrl },
    'Gmail Thread': { url: `https://mail.google.com/mail/u/0/#inbox/${emailData.threadId}` },
    'Estimate': { rich_text: [{ text: { content: extraction.estimatedTime } }] }
  },
  children: [
    {
      type: 'callout',
      callout: {
        rich_text: [{ text: { content: `From: ${emailData.from}\nDate: ${emailData.date}` } }],
        icon: { emoji: '📧' }
      }
    },
    {
      type: 'paragraph',
      paragraph: {
        rich_text: [{ text: { content: emailData.body } }]
      }
    }
  ]
});
```

### 5. Create Calendar Time Block (Optional)

```javascript
// n8n Workflow Node 5: Google Calendar MCP Integration
if (extraction.deadline && extraction.estimatedTime) {
  // Find optimal time slot
  const timeSlot = await findOptimalTimeSlot({
    duration: parseTimeEstimate(extraction.estimatedTime),
    deadline: extraction.deadline,
    priority: extraction.priority
  });

  const calendarEvent = await mcp.calendar.createEvent({
    summary: `📋 ${extraction.mainAction}`,
    description: `Email: ${emailData.subject}
From: ${emailData.from}

Trello: ${trelloCard.shortUrl}
Notion: ${notionTask.url}
Gmail: https://mail.google.com/mail/u/0/#inbox/${emailData.id}
`,
    start: {
      dateTime: timeSlot.start.toISOString(),
      timeZone: context.timezone
    },
    end: {
      dateTime: timeSlot.end.toISOString(),
      timeZone: context.timezone
    },
    colorId: getColorByPriority(extraction.priority),
    reminders: {
      useDefault: false,
      overrides: [
        { method: 'popup', minutes: 15 }
      ]
    }
  });
}
```

### 6. Update Gmail Thread

```javascript
// n8n Workflow Node 6: Update Gmail
// Remove "Action Required" label, add "Converted to Task"
await mcp.gmail.modifyMessage({
  id: emailData.id,
  removeLabelIds: [getLabelId('Action Required')],
  addLabelIds: [getLabelId('Converted to Task')]
});

// Add label with link to Trello card
await mcp.gmail.createLabel({
  name: `Task: ${trelloCard.shortId}`,
  messageListVisibility: 'show',
  labelListVisibility: 'labelShow'
});
```

### 7. Confirmation & Summary

```
✓ Email converted to task successfully

📧 Email: "Project deadline moved to Friday"
👤 From: client@acmecorp.com
📅 Date: Jan 21, 2025 2:15 PM

🎯 Action Extracted:
"Reschedule project tasks to align with new Friday deadline"

📋 Created Across Tools:
  ✓ Trello: "Reschedule project tasks..." (Priority: High)
    Board: Client Projects
    List: This Week
    Due: Jan 24, 2025
    Checklist: 3 subtasks
    Link: https://trello.com/c/abc123

  ✓ Notion: Task in Tasks database
    Status: To Do
    Priority: High
    Linked: Trello, Gmail, Calendar
    Link: https://notion.so/task-xyz789

  ✓ Calendar: Time blocked
    When: Jan 22, 2025 9:00 AM - 11:00 AM (2 hours)
    Reminders: 15 min before
    Link: https://calendar.google.com/event/def456

  ✓ Gmail: Label updated
    Removed: "Action Required"
    Added: "Converted to Task" + "Task: abc123"

Sub-Tasks Identified (3):
  1. Review current project timeline
  2. Identify tasks that can be accelerated
  3. Communicate changes to team

Estimated Time: 2 hours
Deadline: Jan 24, 2025 (Friday)

Time Saved: 8 minutes (vs manual task creation)

Quick Actions:
[1] View in Trello → Opens card
[2] View in Notion → Opens task
[3] Start work now → Opens calendar event
[4] Reply to email → Compose reply
```

## Smart Features

### Context-Aware Priority

```javascript
const determinePriority = (email, extraction) => {
  // Check sender importance
  if (context.email_triage.urgent_senders.some(s => email.from.includes(s))) {
    return 'urgent';
  }

  // Check subject keywords
  if (email.subject.match(/urgent|asap|critical|emergency/i)) {
    return 'urgent';
  }

  // Check deadline proximity
  if (extraction.deadline) {
    const daysUntil = daysBetween(new Date(), new Date(extraction.deadline));
    if (daysUntil <= 2) return 'urgent';
    if (daysUntil <= 7) return 'high';
  }

  // AI-determined priority
  return extraction.priority;
};
```

### Duplicate Detection

```javascript
// Check if task already exists
const existingTask = await mcp.trello.searchCards({
  query: email.subject,
  idBoards: [getCurrentBoardId()]
});

if (existingTask.length > 0) {
  console.warn(`⚠️  Similar task already exists: ${existingTask[0].name}`);
  console.log(`   Link to existing: ${existingTask[0].shortUrl}`);
  console.log(`   Create anyway? (y/n)`);
}
```

### Email Thread Tracking

```javascript
// Link all tasks from same email thread
const threadTasks = await findTasksByThread(email.threadId);

if (threadTasks.length > 0) {
  await mcp.trello.createAttachment({
    idCard: trelloCard.id,
    name: `Related tasks in this thread (${threadTasks.length})`,
    url: threadTasks[0].shortUrl
  });
}
```

## Integration with Other Commands

### With /email:triage

Automatic workflow:

```bash
# Morning email triage identifies action-required emails
# → /workflow:email-to-task automatically triggered
# → Tasks created across all tools
```

### With /calendar:sync-tasks

Time blocking:

```bash
# Email → Task created with deadline
# → /calendar:sync-tasks schedules optimal time
# → Calendar event with reminders
```

### With /find

Universal search:

```bash
# Search by email subject, sender, or content
/find "client deadline"
# Returns: Email, Trello card, Notion task, Calendar event
```

## n8n Workflow Architecture

```
┌─────────────────────────────────────────────┐
│  TRIGGER: Gmail Label "Action Required"    │
│  OR Manual /workflow:email-to-task         │
└─────────────┬───────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────┐
│  NODE 1: Fetch Email (Gmail MCP)           │
│  - Get full email content                   │
│  - Extract headers and body                 │
└─────────────┬───────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────┐
│  NODE 2: AI Extract Action (Claude)        │
│  - Main action item                         │
│  - Sub-tasks                                │
│  - Deadline, priority, estimate             │
└─────────────┬───────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────┐
│  NODE 3: Parallel Task Creation             │
│  ├─ Create Trello card (with checklist)     │
│  ├─ Save to Notion tasks database           │
│  └─ Create calendar time block              │
└─────────────┬───────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────┐
│  NODE 4: Cross-Link Everything              │
│  - Link Trello ↔ Notion ↔ Calendar ↔ Gmail │
│  - Update Gmail labels                      │
└─────────────┬───────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────┐
│  NODE 5: Index for Search                   │
│  - Add to universal search index            │
│  - Link related content                     │
└─────────────────────────────────────────────┘
```

## Business Value

**Time Savings**:

- Manual task creation from email: 5-10 min
- Automated with this workflow: <1 min
- **Saves 30-45 min/day = 3.5-5 hours/week**

**Productivity Gains**:

- Never miss action items from emails
- Everything linked and cross-referenced
- Optimal time blocking automatically
- Searchable across all tools

**Email Management**:

- Reduce inbox clutter
- Clear action vs reference emails
- Archive with confidence (tasks preserved)

## Success Metrics

✅ Task extraction accuracy >90%
✅ Multi-tool creation success >98%
✅ Duplicate detection accuracy >85%
✅ Processing time <30 seconds per email
✅ User satisfaction with extracted actions >8/10

## Security & Privacy

- Email content processed by Claude AI (Anthropic)
- No email content stored permanently (only task description)
- OAuth 2.0 for all tool access
- Audit logging of all conversions

## Troubleshooting

### Action Not Extracted

```bash
# Email too vague for AI to extract action
Solution: Add manual task description
/workflow:email-to-task --email-id msg_123 --action "Custom action description"
```

### Task Created in Wrong Board/Database

```bash
# Override auto-routing
/workflow:email-to-task --email-id msg_123 --board "Client Projects"
```

### Duplicate Tasks Created

```bash
# Improve duplicate detection threshold
/workflow:email-to-task --duplicate-threshold 0.8
```

## Related Commands

- `/email:triage` - Morning email automation
- `/trello:card` - Trello card management
- `/notion:save-note` - Notion note capture
- `/calendar:sync-tasks` - Task → Calendar sync
- `/find` - Universal search

## Notes

**First Use**: Requires Gmail, Trello, and Notion integrations configured.

**Cost**: ~$0.02-0.05 per email conversion (AI extraction + multi-tool operations).

**Accuracy**: AI extraction improves over time with feedback and corrections.

---

*Never lose an action item buried in email again. Automatic email → task conversion across all your tools.*
