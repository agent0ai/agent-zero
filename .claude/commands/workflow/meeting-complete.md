---
description: Meeting → Note → Task automation - captures notes, extracts action items, links everything
argument-hint: "<meeting-name> [--notes <text|file>] [--attendees <list>]"
model: claude-3-5-sonnet-20241022
allowed-tools:
  - Bash
  - Read
  - Write
  - AskUserQuestion
---

# Meeting Complete Workflow Automation

## Overview

**HIGH VALUE WORKFLOW** - Saves 10-15 min per meeting (5-7 hours/week)

End-of-meeting workflow that captures notes, extracts action items, saves decisions to Notion, creates Trello cards, and links everything together automatically.

**Part of Phase 2**: Workflow automation for productivity integration

## What This Command Does

**Trigger**: End of calendar meeting OR manual execution

**Automation**:

1. ✅ Prompts for or captures meeting notes
2. ✅ AI extracts action items → creates Trello cards
3. ✅ AI extracts decisions → saves to Notion
4. ✅ Links meeting note, tasks, calendar event
5. ✅ Updates knowledge base
6. ✅ Sends summary to attendees (optional)

**Time Saved**: 10-15 min per meeting = **5-7 hours/week**

## Usage

```bash
# Auto-trigger at end of calendar meeting
# (runs automatically)

# Manual execution
/workflow:meeting-complete "Team Standup"

# With notes from file
/workflow:meeting-complete "Team Standup" --notes /path/to/notes.md

# With notes from clipboard
/workflow:meeting-complete "Client Review" --notes-from-clipboard

# Interactive mode (prompts for all details)
/workflow:meeting-complete --interactive

# Preview without creating tasks
/workflow:meeting-complete "Team Standup" --dry-run
```

## Automatic Trigger Setup

### Calendar Event Automation

```bash
# Trigger 5 minutes after calendar event ends
# Detects via Google Calendar webhook or cron check
# Prompts user: "Meeting just ended. Capture notes?"
```

## Step-by-Step Execution

### 1. Load Meeting Context

```javascript
// n8n Workflow Node 1: Google Calendar MCP
const meeting = await mcp.calendar.getEvent({
  eventId: eventId || findRecentMeeting(meetingName)
});

const meetingContext = {
  title: meeting.summary,
  start: meeting.start.dateTime,
  end: meeting.end.dateTime,
  duration: calculateDuration(meeting.start, meeting.end),
  attendees: meeting.attendees ? meeting.attendees.map(a => a.email) : [],
  location: meeting.location || 'Virtual',
  calendarLink: meeting.htmlLink
};
```

### 2. Capture Meeting Notes

```javascript
// n8n Workflow Node 2: Collect Notes
let notes;

if (options.notes) {
  // Notes provided via parameter or file
  notes = typeof options.notes === 'string' && options.notes.startsWith('/')
    ? readFile(options.notes)
    : options.notes;
} else {
  // Interactive prompt
  notes = await prompt({
    message: `Meeting notes for "${meetingContext.title}":`,
    multiline: true,
    hint: "Enter notes, then press Ctrl+D (or Ctrl+Z on Windows) when done"
  });
}

const notesData = {
  raw: notes,
  wordCount: notes.split(/\s+/).length,
  timestamp: new Date().toISOString()
};
```

### 3. AI Extract Action Items & Decisions

```javascript
// n8n Workflow Node 3: Claude AI Extraction
const extraction = await claude.extract({
  prompt: `Analyze these meeting notes and extract:

  Meeting: ${meetingContext.title}
  Date: ${meetingContext.start}
  Attendees: ${meetingContext.attendees.join(', ')}

  Notes:
  ${notesData.raw}

  Extract:
  1. **Action Items**: Specific tasks assigned to people
     - Who is responsible
     - What needs to be done
     - By when (deadline)
     - Priority

  2. **Decisions Made**: Key decisions or agreements

  3. **Discussion Topics**: Main topics covered

  4. **Next Steps**: Overall next steps for the team

  Return JSON:
  {
    "actionItems": [
      {
        "task": "Clear action description",
        "assignee": "person@email.com" or "Team" or "TBD",
        "deadline": "2025-02-01" or null,
        "priority": "high|medium|low"
      }
    ],
    "decisions": [
      {
        "decision": "What was decided",
        "rationale": "Why",
        "impactAreas": ["Product", "Marketing"]
      }
    ],
    "topicsDiscussed": ["Topic 1", "Topic 2"],
    "nextSteps": "Overall next steps"
  }
  `
});
```

### 4. Create Trello Cards for Action Items

```javascript
// n8n Workflow Node 4: Trello MCP Integration
const trelloCards = [];

for (const actionItem of extraction.actionItems) {
  const card = await mcp.trello.createCard({
    name: actionItem.task,
    desc: `From meeting: ${meetingContext.title}
Date: ${new Date(meetingContext.start).toLocaleDateString()}
Assignee: ${actionItem.assignee}
Deadline: ${actionItem.deadline || 'Not specified'}

Meeting Notes: [Link will be added]
Calendar: ${meetingContext.calendarLink}
`,
    idList: getListByPriority(actionItem.priority),
    due: actionItem.deadline ? new Date(actionItem.deadline).toISOString() : null,
    idLabels: [getLabelId('from-meeting'), getLabelId(actionItem.priority)],
    pos: 'top'
  });

  // Assign member if email matches Trello user
  if (actionItem.assignee !== 'TBD' && actionItem.assignee !== 'Team') {
    const member = await findTrelloMember(actionItem.assignee);
    if (member) {
      await mcp.trello.addMemberToCard({
        idCard: card.id,
        idMember: member.id
      });
    }
  }

  trelloCards.push(card);
}
```

### 5. Save Meeting Note to Notion

```javascript
// n8n Workflow Node 5: Notion MCP Integration
const notionPage = await mcp.notion.createPage({
  parent: {
    database_id: context.integrations.notion.database_ids.meetings
  },
  properties: {
    Name: { title: [{ text: { content: meetingContext.title } }] },
    Date: { date: { start: meetingContext.start } },
    Duration: { number: meetingContext.duration },
    Attendees: {
      multi_select: meetingContext.attendees.map(email => ({
        name: email.split('@')[0]
      }))
    },
    'Action Items Count': { number: extraction.actionItems.length },
    'Decisions Count': { number: extraction.decisions.length },
    'Calendar Link': { url: meetingContext.calendarLink }
  },
  children: [
    // Meeting metadata
    {
      type: 'callout',
      callout: {
        rich_text: [{ text: { content: `
📅 ${new Date(meetingContext.start).toLocaleString()}
⏱️ Duration: ${meetingContext.duration} minutes
👥 Attendees: ${meetingContext.attendees.length}
        ` } }],
        icon: { emoji: '📝' }
      }
    },

    // Topics discussed
    {
      type: 'heading_2',
      heading_2: { rich_text: [{ text: { content: 'Topics Discussed' } }] }
    },
    ...extraction.topicsDiscussed.map(topic => ({
      type: 'bulleted_list_item',
      bulleted_list_item: {
        rich_text: [{ text: { content: topic } }]
      }
    })),

    // Decisions made
    {
      type: 'heading_2',
      heading_2: { rich_text: [{ text: { content: 'Decisions Made' } }] }
    },
    ...extraction.decisions.map(dec => ({
      type: 'toggle',
      toggle: {
        rich_text: [{ text: { content: dec.decision, annotations: { bold: true } } }],
        children: [
          {
            type: 'paragraph',
            paragraph: {
              rich_text: [{ text: { content: `Rationale: ${dec.rationale}` } }]
            }
          },
          {
            type: 'paragraph',
            paragraph: {
              rich_text: [{ text: { content: `Impact: ${dec.impactAreas.join(', ')}` } }]
            }
          }
        ]
      }
    })),

    // Action items
    {
      type: 'heading_2',
      heading_2: { rich_text: [{ text: { content: 'Action Items' } }] }
    },
    ...trelloCards.map(card => ({
      type: 'to_do',
      to_do: {
        rich_text: [{ text: { content: `${card.name} - ${card.desc.match(/Assignee: (.+)/)[1]}` } }],
        checked: false
      }
    })),

    // Full notes
    {
      type: 'heading_2',
      heading_2: { rich_text: [{ text: { content: 'Full Notes' } }] }
    },
    {
      type: 'paragraph',
      paragraph: {
        rich_text: [{ text: { content: notesData.raw } }]
      }
    },

    // Links
    {
      type: 'divider',
      divider: {}
    },
    {
      type: 'callout',
      callout: {
        rich_text: [{ text: { content: `
🔗 Calendar Event: ${meetingContext.calendarLink}
📋 Trello Cards: ${trelloCards.length} created
        ` } }],
        icon: { emoji: '🔗' }
      }
    }
  ]
});
```

### 6. Cross-Link Everything

```javascript
// n8n Workflow Node 6: Update All Links
// Update Trello cards with Notion link
for (const card of trelloCards) {
  await mcp.trello.updateCard({
    id: card.id,
    desc: card.desc.replace('[Link will be added]', notionPage.url)
  });
}

// Update calendar event description
await mcp.calendar.updateEvent({
  eventId: meeting.id,
  description: `${meeting.description || ''}

Meeting Notes: ${notionPage.url}
Action Items (${trelloCards.length}):
${trelloCards.map(c => `• ${c.name}: ${c.shortUrl}`).join('\n')}
`
});
```

### 7. Save to Local Knowledge Base

```javascript
// n8n Workflow Node 7: Local KB Sync
const localPath = `/knowledge/meetings/${meetingContext.start.split('T')[0]}-${sanitize(meetingContext.title)}.md`;

const markdown = `---
meeting: ${meetingContext.title}
date: ${meetingContext.start}
duration: ${meetingContext.duration} minutes
attendees: ${meetingContext.attendees.join(', ')}
notion_url: ${notionPage.url}
calendar_url: ${meetingContext.calendarLink}
action_items: ${extraction.actionItems.length}
decisions: ${extraction.decisions.length}
---

# ${meetingContext.title}

**Date**: ${new Date(meetingContext.start).toLocaleString()}
**Duration**: ${meetingContext.duration} minutes
**Attendees**: ${meetingContext.attendees.join(', ')}

## Topics Discussed

${extraction.topicsDiscussed.map(t => `- ${t}`).join('\n')}

## Decisions Made

${extraction.decisions.map(d => `
### ${d.decision}

**Rationale**: ${d.rationale}
**Impact Areas**: ${d.impactAreas.join(', ')}
`).join('\n')}

## Action Items

${extraction.actionItems.map((a, i) => `
${i + 1}. **${a.task}**
   - Assignee: ${a.assignee}
   - Deadline: ${a.deadline || 'Not specified'}
   - Priority: ${a.priority}
   - Trello: ${trelloCards[i].shortUrl}
`).join('\n')}

## Full Notes

${notesData.raw}

---

## Links

- [Notion Meeting Note](${notionPage.url})
- [Calendar Event](${meetingContext.calendarLink})
${trelloCards.map(c => `- [Trello: ${c.name}](${c.shortUrl})`).join('\n')}

*Meeting notes captured and processed by Claude Code*
`;

await writeFile(localPath, markdown);
```

### 8. Send Summary to Attendees (Optional)

```javascript
// n8n Workflow Node 8: Gmail MCP (Optional)
if (context.meeting_settings.send_summary_to_attendees) {
  const summary = generateEmailSummary(meetingContext, extraction, notionPage.url);

  await mcp.gmail.send({
    to: meetingContext.attendees.join(','),
    subject: `Meeting Summary: ${meetingContext.title}`,
    body: summary
  });
}
```

### 9. Confirmation

```
✓ Meeting workflow complete

📝 Team Standup - Jan 22, 2025 9:00 AM
⏱️ Duration: 30 minutes
👥 Attendees: 5

📊 Extracted:
  • 3 Action Items
  • 2 Decisions
  • 4 Topics Discussed

📋 Trello Cards Created (3):
  [1] P1: Complete API integration (Assigned: john@team.com)
      Due: Jan 25 | Trello: https://trello.com/c/abc123

  [2] P2: Review design mockups (Assigned: sarah@team.com)
      Due: Jan 24 | Trello: https://trello.com/c/def456

  [3] P3: Update documentation (Assigned: Team)
      Due: Jan 26 | Trello: https://trello.com/c/ghi789

💡 Decisions Logged (2):
  • Launch date moved to Feb 15 (Risk mitigation)
  • Tech stack finalized: React + Node.js (Team consensus)

📝 Meeting Note: https://notion.so/meeting-xyz123
📅 Calendar: Updated with action items
💾 Local: /knowledge/meetings/2025-01-22-team-standup.md

✉️ Summary sent to 5 attendees

Time Saved: 12 minutes (vs manual note-taking and task creation)

Quick Actions:
[1] View in Notion → Opens meeting note
[2] View Trello board → Shows all cards
[3] Schedule next meeting → Creates calendar event
[4] Share with team → Generate share link
```

## Integration with Other Commands

### With /google:calendar

Automatic trigger:

```bash
# Calendar event ends at 10:00 AM
# → Workflow prompts: "Capture notes for Team Standup?"
# → Notes captured and processed
```

### With /meeting:prep

Before/after flow:

```bash
# Before: /meeting:prep "Team Standup"
# → Loads context, agenda, related notes

# After: /workflow:meeting-complete "Team Standup"
# → Saves notes, creates tasks
```

### With /knowledge:capture

Knowledge management:

```bash
# Meeting notes automatically saved to /knowledge/
# → Searchable via /find
# → Linked to related content
```

## Business Value

**Time Savings**:

- Manual note-taking + task creation: 15-20 min
- Automated with this workflow: 3-5 min
- **Saves 10-15 min per meeting = 5-7 hours/week**

**Productivity Gains**:

- Never lose action items from meetings
- Decisions documented and searchable
- Everything linked and cross-referenced
- Automatic follow-up and accountability

**Meeting ROI**:

- Meetings become actionable (not just talk)
- Clear next steps for everyone
- Progress tracking automatic
- Knowledge retained and searchable

## Success Metrics

✅ Note capture time <3 minutes
✅ Action item extraction accuracy >85%
✅ Decision extraction accuracy >90%
✅ Multi-tool sync success >98%
✅ User satisfaction >8/10

## Security & Privacy

- Meeting notes processed by Claude AI (Anthropic)
- Notes stored securely in Notion + Local KB
- OAuth 2.0 for all tool access
- Attendee emails not shared externally

## Troubleshooting

### Action Items Not Extracted

```bash
# Notes too vague for AI extraction
Solution: Use --action-items flag to manually specify
/workflow:meeting-complete "Team Standup" --action-items "Task 1, Task 2"
```

### Wrong Attendees Assigned

```bash
# Override AI assignment
/workflow:meeting-complete "Meeting" --assign-to "john@team.com, sarah@team.com"
```

## Related Commands

- `/meeting:prep` - Pre-meeting preparation
- `/meeting:notes` - Real-time note capture
- `/trello:card` - Trello card management
- `/notion:save-note` - Notion note capture
- `/google:calendar` - Calendar management
- `/find` - Universal search

## Notes

**First Use**: Requires Google Calendar, Trello, and Notion integrations.

**Cost**: ~$0.05-0.10 per meeting (AI extraction + multi-tool operations).

**Accuracy**: AI extraction improves with meeting note structure and clarity.

---

*Transform meetings from time sinks into actionable, documented progress.*
