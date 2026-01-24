---
description: Trello card/task management with Notion and Calendar sync
argument-hint: "<action> <card-name> [--board <name>] [--list <name>] [--due <date>]"
model: claude-3-5-haiku-20241022
allowed-tools:
  - Bash
  - Read
  - Write
  - AskUserQuestion
---

# Trello Card Management Command

## Overview

Create and manage Trello cards with automatic sync to Notion and Google Calendar. Provides unified task management across all productivity tools.

## Actions

**create** - Create new card

```bash
/trello:card create "Replace broken window" --board "Property Maintenance"
/trello:card create "Client proposal" --board "Sales Pipeline" --due "2025-02-01"
```

**update** - Update card

```bash
/trello:card update "Replace broken window" --status "Doing"
/trello:card update "Client proposal" --add-label "urgent"
```

**move** - Move card to different list

```bash
/trello:card move "Replace broken window" --to "Done"
```

**list** - List cards

```bash
/trello:card list --board "Property Maintenance"
/trello:card list --me --status "Doing"
```

## Implementation Details

### MCP Server Required

Requires Trello MCP server:

```bash
/mcp:install trello --auth-type api-key
# Or via Composio
/mcp:install composio --add-integration trello
```

### Context Integration

```json
{
  "integrations": {
    "trello": {
      "enabled": true,
      "board_ids": {
        "primary": "board-123",
        "maintenance": "board-456",
        "projects": "board-789"
      },
      "mcp_server": "trello-mcp"
    },
    "trello_settings": {
      "sync_to_notion": true,
      "sync_to_calendar": true,
      "default_board": "primary"
    }
  }
}
```

## Step-by-Step Execution (Create)

### 1. Determine Target Board

```javascript
let boardId;

if (options.board) {
  boardId = context.integrations.trello.board_ids[options.board];
} else {
  // Use default board
  boardId = context.integrations.trello.board_ids[
    context.trello_settings.default_board
  ];
}

// Get board lists
const lists = await mcp.trello.getLists({ boardId });
const targetList = lists.find(l => l.name === (options.list || 'To Do'));
```

### 2. Create Trello Card

```javascript
const card = await mcp.trello.createCard({
  name: cardName,
  desc: cardDescription || '',
  idList: targetList.id,
  due: options.due ? new Date(options.due).toISOString() : null,
  pos: 'top', // Add to top of list
  idLabels: options.labels ? getLabelIds(options.labels) : []
});
```

### 3. Sync to Notion (Optional)

```javascript
if (context.trello_settings.sync_to_notion) {
  // Create corresponding Notion task
  const notionTask = await mcp.notion.createPage({
    parent: {
      database_id: context.integrations.notion.database_ids.tasks
    },
    properties: {
      Name: { title: [{ text: { content: cardName } }] },
      Status: { select: { name: listToNotionStatus(targetList.name) } },
      'Trello Card': { url: card.shortUrl },
      'Trello Board': { select: { name: getBoardName(boardId) } },
      Due: options.due ? { date: { start: options.due } } : null,
      Source: { select: { name: 'Trello' } }
    }
  });

  // Link back to Notion
  await mcp.trello.updateCard({
    id: card.id,
    desc: card.desc + `\n\nNotion: ${notionTask.url}`
  });
}
```

### 4. Add to Google Calendar (Optional)

```javascript
if (context.trello_settings.sync_to_calendar && options.due) {
  // Create calendar event for due date
  const calendarEvent = await mcp.calendar.createEvent({
    summary: `📋 ${cardName}`,
    description: `Trello: ${card.shortUrl}${notionTask ? `\nNotion: ${notionTask.url}` : ''}`,
    start: {
      date: options.due // All-day event
    },
    end: {
      date: options.due
    },
    colorId: '5', // Yellow for tasks
    reminders: {
      useDefault: false,
      overrides: [
        { method: 'email', minutes: 24 * 60 }, // 1 day before
        { method: 'popup', minutes: 60 } // 1 hour before
      ]
    }
  });

  // Link calendar event to card
  await mcp.trello.updateCard({
    id: card.id,
    desc: card.desc + `\nCalendar: ${calendarEvent.htmlLink}`
  });
}
```

### 5. Create Related Checklist

```javascript
// If task is complex, create checklist
if (options.checklist || isComplexTask(cardName)) {
  const subtasks = await claude.generateSubtasks({
    prompt: `Break down this task into 3-5 subtasks:

    Task: ${cardName}
    Context: ${context.name}
    Due: ${options.due}

    Generate actionable subtasks.`
  });

  await mcp.trello.createChecklist({
    idCard: card.id,
    name: 'Subtasks',
    checkItems: subtasks.map(st => ({ name: st.name }))
  });
}
```

### 6. Confirmation

```
✓ Trello card created

📋 "Replace broken window"
📁 Board: Property Maintenance
📝 List: To Do
📅 Due: Feb 15, 2025
🏷️  Labels: maintenance, urgent

🔗 Trello: https://trello.com/c/abc123
🔗 Notion: https://notion.so/task-xyz789
📅 Calendar: Feb 15, 2025 (with reminders)

✅ Checklist (4 items):
  [ ] Get quotes from contractors
  [ ] Schedule repair appointment
  [ ] Notify tenant of work
  [ ] Verify completion and payment

Synced To:
  ✓ Notion tasks database
  ✓ Google Calendar
  ✓ Local task system

Next Actions:
[1] View in Trello → Opens card
[2] Start task → Moves to "Doing"
[3] Add attachment → Upload file
[4] Assign member → Assign to team
```

## Smart Features

### Auto-Categorization

```javascript
// Auto-select board based on card content
const determineBoard = (cardName, context) => {
  if (cardName.match(/maintenance|repair|fix/i)) {
    return context.integrations.trello.board_ids.maintenance;
  }
  if (cardName.match(/project|initiative/i)) {
    return context.integrations.trello.board_ids.projects;
  }
  if (cardName.match(/client|proposal|sales/i)) {
    return context.integrations.trello.board_ids.sales;
  }
  return context.integrations.trello.board_ids.primary;
};
```

### Dependency Tracking

```javascript
// Link related cards
if (options.blockedBy) {
  await mcp.trello.createAttachment({
    idCard: card.id,
    name: `Blocked by: ${options.blockedBy}`,
    url: getCardUrl(options.blockedBy)
  });
}
```

### Time Tracking

```javascript
// Add time estimate and tracking
if (options.estimate) {
  await mcp.trello.addCustomField({
    idCard: card.id,
    field: 'Time Estimate',
    value: options.estimate
  });

  // Create calendar time block if synced
  if (context.trello_settings.sync_to_calendar) {
    await createTimeBlock(cardName, options.estimate);
  }
}
```

## Board Templates

### Property Maintenance

Lists: Reported → Scheduled → In Progress → Completed → Archived
Labels: urgent, routine, tenant-requested, preventive

### Client Projects

Lists: Leads → Proposals → Active → Review → Completed
Labels: high-value, consulting, development, ongoing

### Personal Tasks

Lists: Inbox → Today → This Week → Someday → Done
Labels: work, personal, urgent, waiting-on

## Integration with Other Commands

### With /workflow:email-to-task

Automatic card creation from emails:

```bash
# Email flagged "Action Required"
# → Trello card created automatically
# → Synced to Notion and Calendar
```

### With /calendar:sync-tasks

Calendar time blocking:

```bash
# Trello cards with due dates
# → Auto-scheduled in calendar
# → Time blocking by priority
```

### With /notion:project

Project task sync:

```bash
# Notion project tasks
# → Trello cards created
# → Bidirectional sync
```

### With /assistant:tasks

Unified task management:

```bash
# Trello cards appear in /assistant:tasks
# Completion syncs everywhere
```

## Business Value

**Time Savings**:

- Card creation: 30 sec vs 2-3 min (manual)
- Multi-tool sync: Automatic (saves 5 min/task)
- Saves 5-10 min/day = **0.8-1.5 hours/week**

**Task Management**:

- Unified across Trello, Notion, Calendar
- Automatic subtask generation
- Dependency tracking
- Time blocking integration

## Success Metrics

✅ Card creation time <30 seconds
✅ Sync success rate >98%
✅ Auto-categorization accuracy >85%
✅ Bidirectional sync <5 seconds

## Security & Privacy

- Trello API Key & Token (encrypted storage)
- Per-context board isolation
- Audit logging of all operations

## Troubleshooting

### MCP Server Not Installed

```bash
Error: Trello MCP server not found

Solution:
/mcp:install trello --auth-type api-key
```

### Board Not Found

```bash
Error: Board "Property Maintenance" not found

Solution:
# List available boards
/trello:list-boards

# Add to context
/context:switch property-management --edit-trello-boards
```

### Sync Failed

```bash
Error: Failed to sync to Notion

Solution:
# Check Notion integration
/mcp:list --detailed

# Retry sync
/trello:card sync --card-id abc123 --to notion,calendar
```

## Advanced Options

### Bulk Operations

```bash
# Create multiple cards from file
/trello:card create --batch /path/to/tasks.txt

# Move multiple cards
/trello:card move --board "Maintenance" --from "To Do" --to "Done" --filter "completed"
```

### Power-Ups Integration

```bash
# Add calendar power-up
/trello:card add-powerup --card "Replace window" --powerup "calendar"

# Add custom fields
/trello:card add-field --card "Client proposal" --field "Revenue" --value "$50000"
```

### Automation Rules

```bash
# Auto-move when checklist complete
/trello:card automation --when "checklist_complete" --then "move_to_done"
```

## Related Commands

- `/notion:save-note` - Quick note capture
- `/notion:project` - Project management
- `/capture` - Universal quick capture
- `/workflow:email-to-task` - Email → Task automation
- `/calendar:sync-tasks` - Task → Calendar sync
- `/find` - Universal search

## Notes

**Sync**: Real-time bidirectional sync between Trello, Notion, and Calendar.

**Offline**: Can create cards offline, syncs when back online.

**Limits**: Trello API rate limit: 300 requests/10 seconds per token.

---

*Master your tasks across Trello, Notion, and Calendar with one command.*
