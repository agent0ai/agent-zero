---
description: Notion project management - create projects with task lists, milestones, and calendar integration
argument-hint: "<action> <project-name> [--start <date>] [--deadline <date>] [--template <name>]"
model: claude-3-5-haiku-20241022
allowed-tools:
  - Bash
  - Read
  - Write
  - AskUserQuestion
---

# Notion Project Management Command

## Overview

Create and manage projects in Notion with automatic task list generation, calendar integration, and Trello sync. Part of the Phase 2 productivity integration.

## Actions

**create** - Create new project

```bash
/notion:project create "Property Renovation - 123 Main" --start "2025-12-01"
```

**update** - Update project status

```bash
/notion:project update "Property Renovation - 123 Main" --status "In Progress"
```

**list** - List all projects

```bash
/notion:project list --status active
```

**archive** - Archive completed project

```bash
/notion:project archive "Property Renovation - 123 Main"
```

## Implementation Details

### MCP Server Required

Requires Notion MCP server:

```bash
/mcp:install notion --auth-type api-token
```

### Context Integration

```json
{
  "integrations": {
    "notion": {
      "enabled": true,
      "database_ids": {
        "projects": "db-projects-789"
      }
    }
  }
}
```

## Step-by-Step Execution (Create)

### 1. Create Project Page

```javascript
const project = await mcp.notion.createPage({
  parent: { database_id: context.integrations.notion.database_ids.projects },
  properties: {
    Name: { title: [{ text: { content: projectName } }] },
    Status: { select: { name: "Planning" } },
    Start Date: { date: { start: startDate } },
    Deadline: deadline ? { date: { start: deadline } } : null,
    Owner: { people: [{ id: context.user_id }] },
    Context: { select: { name: context.name } },
    Priority: { select: { name: determinePriority(deadline) } }
  }
});
```

### 2. Create Task List

```javascript
// AI generates initial task breakdown
const tasks = await claude.generateTasks({
  prompt: `Break down this project into actionable tasks:

  Project: ${projectName}
  Start: ${startDate}
  Deadline: ${deadline}
  Context: ${context.name}

  Generate 5-10 tasks with:
  - Clear action verbs
  - Realistic time estimates
  - Logical dependencies
  - Prioritization
  `
});

// Create task database entries
for (const task of tasks) {
  await mcp.notion.createPage({
    parent: { database_id: context.integrations.notion.database_ids.tasks },
    properties: {
      Name: { title: [{ text: { content: task.name } }] },
      Project: { relation: [{ id: project.id }] },
      Status: { select: { name: "To Do" } },
      Priority: { select: { name: task.priority } },
      Estimate: { number: task.estimateHours }
    }
  });
}
```

### 3. Create Calendar Integration

```javascript
// Add project milestones to Google Calendar
await mcp.calendar.createEvent({
  summary: `🎯 ${projectName} - Start`,
  start: { date: startDate },
  description: `Project started: ${project.url}`,
  colorId: '9' // Blue for projects
});

if (deadline) {
  await mcp.calendar.createEvent({
    summary: `🏁 ${projectName} - Deadline`,
    start: { date: deadline },
    description: `Project deadline: ${project.url}`,
    colorId: '11', // Red for deadlines
    reminders: {
      useDefault: false,
      overrides: [
        { method: 'email', minutes: 24 * 60 * 7 }, // 1 week before
        { method: 'popup', minutes: 24 * 60 } // 1 day before
      ]
    }
  });
}
```

### 4. Create Trello Board (Optional)

```javascript
// If Trello integration enabled, create board
if (context.integrations.trello.enabled) {
  const board = await mcp.trello.createBoard({
    name: projectName,
    defaultLists: true // Creates To Do, Doing, Done
  });

  // Link Notion project to Trello board
  await mcp.notion.updatePage({
    page_id: project.id,
    properties: {
      'Trello Board': { url: board.url }
    }
  });

  // Sync tasks to Trello cards
  for (const task of tasks) {
    await mcp.trello.createCard({
      name: task.name,
      desc: `From Notion: ${project.url}`,
      idList: board.lists.find(l => l.name === 'To Do').id
    });
  }
}
```

### 5. Confirmation

```
✓ Project created in Notion

🎯 Property Renovation - 123 Main St
📅 Start: Dec 1, 2025 | Deadline: Feb 28, 2026
📊 Status: Planning | Priority: High
👤 Owner: You

📝 Tasks Generated (8):
  [1] P1: Hire contractor and get quotes (Est: 4 hrs)
  [2] P1: Create renovation budget and timeline (Est: 2 hrs)
  [3] P2: Obtain necessary permits (Est: 8 hrs)
  [4] P2: Order materials and appliances (Est: 3 hrs)
  [5] P3: Schedule tenant move-out (Est: 1 hr)
  [6] P1: Coordinate with contractors (Est: 10 hrs)
  [7] P2: Conduct progress inspections (Est: 5 hrs)
  [8] P3: Final walkthrough and photos (Est: 2 hrs)

📅 Calendar Events Added:
  • Dec 1: Project start date
  • Feb 28: Project deadline (with reminders)

🔗 Trello Board: https://trello.com/b/abc123
🔗 Notion: https://notion.so/page-xyz789

Next Actions:
[1] View in Notion → Opens project page
[2] View tasks → Lists all 8 tasks
[3] Start first task → Marks task as "In Progress"
[4] Update timeline → Adjusts dates
```

## Project Templates

### Property Renovation

```bash
/notion:project create "Property Renovation" --template property-renovation
```

**Includes**:

- Contractor hiring tasks
- Permit acquisition
- Material ordering
- Inspection scheduling
- Tenant coordination
- Budget tracking

### Client Onboarding

```bash
/notion:project create "Client Onboarding - Acme Corp" --template client-onboarding
```

**Includes**:

- Contract review
- Discovery meeting
- Project scoping
- Proposal creation
- Kickoff meeting
- First deliverable

### Product Launch

```bash
/notion:project create "Product Launch - Q2" --template product-launch
```

**Includes**:

- Market research
- Feature development
- Beta testing
- Marketing campaign
- Launch event
- Post-launch analysis

## Integration with Other Commands

### With /trello:card

Automatic Trello sync:

```bash
# Tasks automatically sync to Trello
# Updates in Trello reflected in Notion
```

### With /google:calendar

Calendar integration:

```bash
# Milestones automatically added to calendar
# Tasks with deadlines create calendar events
```

### With /assistant:tasks

Task management:

```bash
# Notion tasks appear in /assistant:tasks
# Completion syncs both ways
```

### With /dashboard:overview

Project tracking:

```bash
# Active projects shown in dashboard
# Progress and deadline warnings
```

## Business Value

**Time Savings**:

- Project setup: 30 min vs 2-3 hours (manual)
- Task breakdown: AI-generated in seconds
- Calendar integration: Automatic

**Project Management**:

- Consistent project structure
- Automatic task generation
- Multi-tool sync (Notion + Trello + Calendar)
- Progress tracking and reporting

## Success Metrics

✅ Project creation time <2 minutes
✅ AI task generation accuracy >80%
✅ Trello sync success rate >95%
✅ Calendar integration 100% reliable

## Related Commands

- `/notion:save-note` - Quick note capture
- `/trello:card` - Trello card management
- `/google:calendar` - Calendar management
- `/dashboard:overview` - Project dashboard
- `/workflow:meeting-complete` - Meeting → Project notes

## Notes

**Templates**: Custom templates can be defined in context configuration.

**Sync**: Bidirectional sync between Notion, Trello, and Google Calendar.

**Collaboration**: Share Notion project pages with team members.

---

*Manage projects like a pro with AI-powered automation.*
