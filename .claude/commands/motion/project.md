---
description: Motion AI project creation with automatic task scheduling and resource allocation
argument-hint: "<project-name> [--deadline <date>] [--template <name>]"
model: claude-3-5-haiku-20241022
allowed-tools:
  - Bash
  - Read
  - Write
---

# Motion Project Command

## Overview

Create projects in Motion with AI-powered automatic task breakdown and scheduling. Motion AI generates tasks, estimates durations, schedules everything optimally, and adapts as the project progresses.

**Part of Phase 3**: Motion + AI Autopilot integration

## Usage

```bash
# Create project with deadline
/motion:project "Website Redesign" --deadline "2025-03-31"

# Use template
/motion:project "Client Onboarding - Acme Corp" --template client-onboarding

# Let Motion AI plan everything
/motion:project "Property Renovation" --auto-plan
```

## Motion AI Project Planning

Motion's AI handles:

- ✅ Task breakdown (AI generates 10-20 tasks)
- ✅ Duration estimates (based on similar projects)
- ✅ Dependency mapping (task order and blockers)
- ✅ Resource allocation (team member assignment)
- ✅ Optimal scheduling (deadline working backward)
- ✅ Auto-rescheduling (adapts to changes)

## Implementation

### Create Project with AI Task Generation

```javascript
const project = await mcp.motion.createProject({
  name: projectName,
  deadline: deadline,
  workspace: context.integrations.motion.workspace_id
});

// Motion AI generates tasks
const aiTasks = await mcp.motion.generateProjectTasks({
  projectId: project.id,
  context: projectDescription,
  deadline: deadline
});

// Motion AI schedules all tasks optimally
await mcp.motion.scheduleProject({
  projectId: project.id,
  strategy: 'deadline_driven' // works backward from deadline
});
```

### Sync to Notion

```javascript
const notionProject = await mcp.notion.createPage({
  parent: { database_id: context.integrations.notion.database_ids.projects },
  properties: {
    Name: { title: [{ text: { content: projectName } }] },
    Deadline: { date: { start: deadline } },
    'Motion Project': { url: project.web_url },
    'Tasks Count': { number: aiTasks.length },
    Status: { select: { name: 'In Progress' } }
  }
});

// Create linked task pages
for (const task of aiTasks) {
  await mcp.notion.createPage({
    parent: { database_id: context.integrations.notion.database_ids.tasks },
    properties: {
      Name: { title: [{ text: { content: task.name } }] },
      Project: { relation: [{ id: notionProject.id }] },
      'Motion Task': { url: task.web_url },
      Due: { date: { start: task.scheduled_time.start } }
    }
  });
}
```

### Confirmation

```
✓ Project created and AI-scheduled by Motion

🎯 "Website Redesign"
📅 Deadline: March 31, 2025
⏱️  Total Duration: 240 hours (6 weeks)

🤖 Motion AI Generated 18 Tasks:

Phase 1: Discovery & Planning (2 weeks)
  [1] Stakeholder interviews (8 hrs) - Jan 23-24
  [2] Competitive analysis (6 hrs) - Jan 25
  [3] User research (12 hrs) - Jan 27-28
  [4] Requirements doc (10 hrs) - Jan 29-30

Phase 2: Design (2 weeks)
  [5] Wireframes (16 hrs) - Feb 3-5
  [6] UI mockups (20 hrs) - Feb 6-9
  [7] Design review (4 hrs) - Feb 10
  [8] Revisions (12 hrs) - Feb 11-12

Phase 3: Development (2 weeks)
  [9] Frontend setup (8 hrs) - Feb 13-14
  [10] Component library (16 hrs) - Feb 17-19
  [11] Page templates (24 hrs) - Feb 20-24
  [12] Integration (16 hrs) - Feb 25-27

Phase 4: Testing & Launch (1 week)
  [13] QA testing (12 hrs) - Feb 28-Mar 3
  [14] Bug fixes (16 hrs) - Mar 4-6
  [15] Performance optimization (8 hrs) - Mar 7
  [16] Content migration (12 hrs) - Mar 10-11
  [17] Final review (4 hrs) - Mar 12
  [18] Launch (4 hrs) - Mar 13

📊 Project Metrics:
  Total estimated time: 240 hours
  Scheduled across: 6 weeks
  Team members: 3 people
  Critical path: 18 tasks
  Buffer time: 15% (built into schedule)

📅 All tasks synced to Google Calendar
📝 Project created in Notion with task links
🔗 Motion: https://app.usemotion.com/project/abc123

Motion AI will:
  ✓ Auto-reschedule if conflicts arise
  ✓ Alert on deadline risks
  ✓ Suggest resource adjustments
  ✓ Track progress automatically

Next Actions:
[1] View project → Opens Motion
[2] Adjust timeline → Modify deadline
[3] Assign team → Add members
[4] Start first task → Begin work
```

## Related Commands

- `/motion:task` - Individual task creation
- `/motion:schedule` - Weekly optimization
- `/notion:project` - Notion project management

## Notes

**Motion AI**: Learns from completed projects to improve estimates.

---

*Let Motion AI plan your entire project in seconds.*
