---
description: Universal quick capture - intelligently routes content to the right tool (Notion, Trello, Drive, or local KB)
argument-hint: "<content> [--to <notion|trello|drive|local>] [--type <note|task|file|idea>]"
model: claude-3-5-sonnet-20241022
allowed-tools:
  - Bash
  - Read
  - Write
  - AskUserQuestion
---

# Universal Quick Capture Command

## Overview

**ONE COMMAND TO CAPTURE EVERYTHING**

Intelligently routes content to the optimal tool based on type and context. Never think about where to save something - just capture it.

**Part of Phase 2**: Unified productivity integration

## What This Command Does

- ✅ Auto-detects content type (note, task, file, idea, reference)
- ✅ Routes to optimal tool (Notion, Trello, Google Drive, Local KB)
- ✅ Saves to all relevant locations in parallel
- ✅ Creates cross-references and links
- ✅ Indexes for universal search
- ✅ **Saves in <2 seconds**

## Usage

```bash
# Auto-detect and route
/capture "Tenant prefers email for maintenance requests"
# → Saves to Notion (note) + Local KB

# Capture task
/capture "Replace broken window in Unit 2B"
# → Creates Trello card + Notion task + Calendar block

# Capture idea
/capture "Idea: Automate lease renewal reminders"
# → Saves to Notion ideas database + Local KB

# Capture file
/capture /path/to/contract.pdf
# → Uploads to Google Drive + Links in Notion + Saves locally

# Force specific tool
/capture "Important meeting notes" --to notion

# From clipboard
/capture --from-clipboard

# Interactive mode
/capture --interactive
```

## Intelligent Routing Logic

### Content Type Detection

```javascript
const detectContentType = (content) => {
  // Task detection
  if (content.match(/^(todo|task|action item|need to|must|should)/i)) {
    return 'task';
  }
  if (content.match(/(fix|replace|repair|call|email|schedule|complete)/i)) {
    return 'task';
  }

  // Idea detection
  if (content.match(/^(idea|concept|brainstorm|what if|could we)/i)) {
    return 'idea';
  }

  // File detection
  if (content.startsWith('/') || content.startsWith('~')) {
    return 'file';
  }

  // Reference/Link detection
  if (content.match(/^https?:\/\//)) {
    return 'reference';
  }

  // Meeting notes detection
  if (content.match(/(meeting|discussed|attendees|agenda|action items)/i)) {
    return 'meeting_note';
  }

  // Default: Note
  return 'note';
};
```

### Tool Selection Matrix

| Content Type | Primary Tool | Secondary | Local KB |
|--------------|--------------|-----------|----------|
| **Task** | Trello Card | Notion Task | ✓ |
| **Note** | Notion | - | ✓ |
| **Idea** | Notion (Ideas DB) | - | ✓ |
| **File** | Google Drive | Notion Link | ✓ |
| **Reference** | Notion | - | ✓ |
| **Meeting Note** | Notion | Calendar Link | ✓ |

## Step-by-Step Execution

### 1. Parse and Analyze Content

```javascript
// Extract content and metadata
const input = parseInput(content);
const metadata = {
  type: detectContentType(input.content),
  keywords: extractKeywords(input.content),
  context: getCurrentContext(),
  timestamp: new Date().toISOString(),
  source: 'capture-command'
};
```

### 2. Determine Routing

```javascript
// n8n Workflow Node: Intelligent Routing
const routing = await claude.determineRouting({
  prompt: `Determine optimal routing for this content:

  Content: "${input.content}"
  Detected Type: ${metadata.type}
  User Context: ${metadata.context.name}

  Available Tools:
  - Notion (notes, projects, ideas, knowledge base)
  - Trello (tasks, cards, projects)
  - Google Drive (files, documents)
  - Local Knowledge Base (markdown files)

  Return JSON:
  {
    "primary": "notion|trello|drive|local",
    "secondary": ["notion", "local"],
    "database": "specific database name",
    "reasoning": "why this routing"
  }
  `
});
```

### 3. Execute Multi-Tool Capture (Parallel)

```javascript
// n8n Workflow: Parallel execution
const promises = [];

// Primary tool
if (routing.primary === 'notion') {
  promises.push(
    mcp.notion.createPage({
      parent: { database_id: getDatabaseId(routing.database) },
      properties: {
        Name: { title: [{ text: { content: extractTitle(input.content) } }] },
        Type: { select: { name: metadata.type } },
        Content: { rich_text: [{ text: { content: input.content } }] },
        Context: { select: { name: metadata.context.name } },
        Source: { select: { name: 'Capture Command' } },
        Created: { date: { start: metadata.timestamp } }
      }
    })
  );
}

if (routing.primary === 'trello') {
  promises.push(
    mcp.trello.createCard({
      name: extractTitle(input.content),
      desc: input.content,
      idList: getDefaultList(metadata.context),
      pos: 'top'
    })
  );
}

if (routing.primary === 'drive') {
  promises.push(
    mcp.drive.uploadFile({
      localPath: input.content,
      parents: [getDefaultFolder(metadata.context)]
    })
  );
}

// Always save to local KB
promises.push(
  saveToLocalKB({
    content: input.content,
    metadata: metadata,
    path: `/knowledge/captured/${Date.now()}-${sanitize(extractTitle(input.content))}.md`
  })
);

// Execute all in parallel
const results = await Promise.all(promises);
```

### 4. Create Cross-References

```javascript
// Link all saved locations together
const links = {
  notion: results.find(r => r.type === 'notion')?.url,
  trello: results.find(r => r.type === 'trello')?.shortUrl,
  drive: results.find(r => r.type === 'drive')?.webViewLink,
  local: results.find(r => r.type === 'local')?.path
};

// Update each location with links to others
if (links.notion) {
  await mcp.notion.appendBlock({
    block_id: links.notion.id,
    children: [
      {
        type: 'callout',
        callout: {
          rich_text: [{ text: { content: `
Also saved to:
${links.trello ? `• Trello: ${links.trello}` : ''}
${links.drive ? `• Drive: ${links.drive}` : ''}
${links.local ? `• Local: ${links.local}` : ''}
          ` } }],
          icon: { emoji: '🔗' }
        }
      }
    ]
  });
}
```

### 5. Index for Search

```javascript
// Add to search index for /find command
await searchIndex.add({
  id: generateId(),
  content: input.content,
  type: metadata.type,
  sources: {
    notion: links.notion,
    trello: links.trello,
    drive: links.drive,
    local: links.local
  },
  keywords: metadata.keywords,
  context: metadata.context.name,
  timestamp: metadata.timestamp
});
```

### 6. Confirmation

```
✓ Content captured and saved

📝 "Tenant prefers email for maintenance requests"
🏷️  Type: Note
📁 Context: Property Management

Saved To:
  ✓ Notion: Property Notes database
    https://notion.so/page-abc123

  ✓ Local KB: /knowledge/captured/tenant-email-preference.md

  ✓ Search Index: Indexed (findable via /find)

Auto-Tagged: #tenant-communication #preference #maintenance

Related Content Found (3):
  • Email: "Maintenance Request - Unit 2B" (Jan 20)
  • Contact: John Doe (Tenant - Unit 2B)
  • Note: "Unit 2B tenant communication log"

Time: 1.8 seconds

Quick Actions:
[1] Open in Notion → Opens browser
[2] View local copy → Opens in editor
[3] Add to project → Links to existing project
[4] Share → Generate share link
```

## Examples by Content Type

### Capturing a Task

```bash
/capture "Call contractor for HVAC repair quote"
```

**Routes to**:

- Primary: Trello card ("Property Maintenance" board)
- Secondary: Notion task database
- Calendar: Time block created (next available slot)
- Local KB: Saved for reference

### Capturing an Idea

```bash
/capture "Idea: Create automated tenant satisfaction survey"
```

**Routes to**:

- Primary: Notion Ideas database
- Secondary: Local KB `/ideas/` folder
- Tags: #automation #tenant-satisfaction #survey

### Capturing a File

```bash
/capture ~/Documents/lease-agreement-unit-2B.pdf
```

**Routes to**:

- Primary: Google Drive (`Contracts/2025/`)
- Secondary: Notion link (Property Notes)
- Local KB: Reference link saved

### Capturing a Meeting Note

```bash
/capture "Meeting with contractor - discussed timeline, estimated 3 weeks for renovation, budget $25K"
```

**Routes to**:

- Primary: Notion (Meetings database)
- Secondary: Linked to Calendar event (if meeting found)
- Extract: Tasks created ("Get detailed timeline", "Review budget")
- Local KB: Saved for reference

## Integration with Other Commands

### With /knowledge:capture

Enhanced version:

```bash
# /capture is universal version of /knowledge:capture
# Routes intelligently, /knowledge:capture always saves local
```

### With /notion:save-note

Direct routing:

```bash
/capture "Note content" --to notion
# Equivalent to /notion:save-note "Note content"
```

### With /trello:card

Task routing:

```bash
/capture "Task content"
# Auto-detects task, creates Trello card
```

### With /find

Search integration:

```bash
# Everything captured is searchable
/find "tenant email preference"
# Returns all captured content matching query
```

## n8n Workflow Architecture

```
┌─────────────────────────────────────────────┐
│  INPUT: Content from /capture command      │
└─────────────┬───────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────┐
│  NODE 1: Parse & Analyze Content           │
│  - Extract keywords                         │
│  - Detect content type                      │
│  - Get user context                         │
└─────────────┬───────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────┐
│  NODE 2: AI Routing Decision (Claude)      │
│  - Determine primary tool                   │
│  - Determine secondary tools                │
│  - Select database/board/folder             │
└─────────────┬───────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────┐
│  NODE 3: Parallel Save Operations          │
│  ├─ Save to Notion (if selected)            │
│  ├─ Create Trello card (if selected)        │
│  ├─ Upload to Drive (if file)               │
│  └─ Save to local KB (always)               │
└─────────────┬───────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────┐
│  NODE 4: Create Cross-References            │
│  - Link all saved locations                 │
│  - Update with related content              │
└─────────────┬───────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────┐
│  NODE 5: Index for Search                   │
│  - Add to search index                      │
│  - Tag with keywords                        │
│  - Link related content                     │
└─────────────────────────────────────────────┘
```

## Business Value

**Time Savings**:

- No more "where should I save this?" decisions
- Capture in <2 seconds vs 30-60 seconds (manual)
- Saves 5-10 min/day = **0.8-1.5 hours/week**

**Productivity Gains**:

- Never lose information again
- Everything automatically organized
- Searchable across all tools
- Cross-referenced and linked

**Cognitive Load Reduction**:

- One command for everything
- No tool context switching
- Automatic categorization
- Smart routing

## Success Metrics

✅ Capture time <2 seconds
✅ Routing accuracy >90%
✅ Multi-tool save success >98%
✅ Cross-reference creation 100%
✅ Search indexing <5 seconds

## Security & Privacy

- Per-context tool isolation
- Encrypted credential storage
- Local KB always saved (offline backup)
- Audit logging of all captures

## Troubleshooting

### Wrong Tool Selected

```bash
# Override auto-routing
/capture "Content" --to notion

# Train AI on your preferences
/capture --learn-from-correction
```

### Save Failed

```bash
# Retry with specific tool
/capture --retry-last --to trello

# Check tool availability
/mcp:list --test-connections
```

## Advanced Options

### Batch Capture

```bash
# Capture multiple items from file
/capture --batch /path/to/items.txt
```

### Scheduled Capture

```bash
# Capture at specific time
/capture "Weekly review" --schedule "Friday 4pm"
```

### Voice Capture

```bash
# Capture from voice note (requires transcription)
/capture --voice /path/to/recording.mp3
```

## Related Commands

- `/notion:save-note` - Notion-specific capture
- `/trello:card` - Trello-specific capture
- `/google:drive upload` - Drive-specific upload
- `/knowledge:capture` - Local KB capture
- `/find` - Universal search across all captured content

## Notes

**First Use**: Requires at least one integration (Notion, Trello, or Drive) configured.

**Performance**: Parallel saves complete in <2 seconds total.

**Offline**: Can save locally when offline, syncs to cloud tools when back online.

**Cost**: ~$0.01-0.02 per capture (AI routing + multi-tool operations).

---

*One command to capture everything. Never lose an idea, task, or note again.*
