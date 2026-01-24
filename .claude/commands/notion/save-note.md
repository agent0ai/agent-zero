---
description: Quick capture to Notion - save notes, ideas, and information to Notion databases
argument-hint: "<note-content> [--database <name>] [--tags <comma-separated>]"
model: claude-3-5-haiku-20241022
allowed-tools:
  - Bash
  - Read
  - Write
  - AskUserQuestion
---

# Notion Quick Capture Command

## Overview

Instantly capture notes, ideas, and information to Notion databases with automatic categorization, tagging, and bidirectional sync to local knowledge base.

**Part of Phase 2**: Notion + Trello integration for knowledge and task management

## What This Command Does

- ✅ Save quick notes to Notion databases (<2 seconds)
- ✅ Auto-categorize by content type (meeting note, idea, task, reference)
- ✅ Apply smart tags and properties
- ✅ Sync to local markdown knowledge base
- ✅ Link to related content (emails, calendar events, tasks)
- ✅ Full-text search indexing

## Usage

```bash
# Quick note to default database
/notion:save-note "Tenant prefers email for maintenance requests"

# Save to specific database
/notion:save-note "Q1 revenue target: $150K" --database "Business Goals"

# With tags
/notion:save-note "Research: AI automation tools" --tags "research,automation,ai"

# From clipboard
/notion:save-note --from-clipboard

# From file
/notion:save-note --from-file /path/to/notes.md

# Interactive mode (prompts for details)
/notion:save-note --interactive
```

## Implementation Details

### MCP Server Required

This command requires **Notion MCP** to be installed:

```bash
# Install Notion MCP server
/mcp:install notion --auth-type api-token

# Or via Composio (if already using for Google Workspace)
/mcp:install composio --add-integration notion
```

### Authentication

Uses Notion Integration Token:

- Create integration at: <https://www.notion.so/my-integrations>
- Grant access to databases
- Token stored in `~/.mcp/auth/notion.json` (encrypted)

### Context Integration

Automatically uses Notion workspace from active context:

```json
{
  "name": "property-management",
  "integrations": {
    "notion": {
      "enabled": true,
      "workspace_id": "workspace-123",
      "database_ids": {
        "notes": "db-notes-456",
        "projects": "db-projects-789",
        "contacts": "db-contacts-012",
        "knowledge_base": "db-kb-345"
      },
      "mcp_server": "notion-mcp"
    }
  },
  "notion_settings": {
    "default_database": "notes",
    "auto_sync_to_local": true,
    "auto_tag": true,
    "link_related_content": true
  }
}
```

## Step-by-Step Execution

### 1. Parse Note Content

```javascript
// Extract content and metadata
const content = parseNoteContent(input);
const metadata = {
  type: detectContentType(content), // meeting, idea, task, reference
  tags: extractTags(content),
  links: extractLinks(content),
  mentions: extractMentions(content)
};
```

### 2. Determine Target Database

```javascript
// Use specified database or auto-detect
let databaseId;

if (options.database) {
  databaseId = context.integrations.notion.database_ids[options.database];
} else {
  // Auto-detect based on content
  databaseId = autoDetectDatabase(metadata.type, content);
}
```

### 3. Create Notion Page

```javascript
// Create page via MCP
const page = await mcp.notion.createPage({
  parent: { database_id: databaseId },
  properties: {
    Name: {
      title: [{ text: { content: extractTitle(content) } }]
    },
    Type: {
      select: { name: metadata.type }
    },
    Tags: {
      multi_select: metadata.tags.map(tag => ({ name: tag }))
    },
    Created: {
      date: { start: new Date().toISOString() }
    },
    Source: {
      select: { name: `Claude Code (${context.name})` }
    },
    Context: {
      select: { name: context.name }
    }
  },
  children: [
    {
      object: 'block',
      type: 'paragraph',
      paragraph: {
        rich_text: [{ text: { content: content } }]
      }
    }
  ]
});
```

### 4. Link Related Content

```javascript
// Link to related emails, calendar events, tasks
if (context.notion_settings.link_related_content) {
  const relatedContent = await findRelatedContent(content, metadata);

  for (const item of relatedContent) {
    await mcp.notion.appendBlock({
      block_id: page.id,
      children: [
        {
          type: 'callout',
          callout: {
            rich_text: [{ text: { content: `Related: ${item.title}` } }],
            icon: { emoji: getIconForType(item.type) }
          }
        }
      ]
    });
  }
}
```

### 5. Sync to Local Knowledge Base

```javascript
// Create local markdown copy
if (context.notion_settings.auto_sync_to_local) {
  const localPath = `/knowledge/notion/${sanitizeFilename(page.properties.Name.title[0].text.content)}.md`;

  const markdown = `---
notion_id: ${page.id}
notion_url: ${page.url}
type: ${metadata.type}
tags: ${metadata.tags.join(', ')}
created: ${new Date().toISOString()}
context: ${context.name}
---

# ${page.properties.Name.title[0].text.content}

${content}

## Related Content
${relatedContent.map(item => `- [${item.title}](${item.url})`).join('\n')}

---
*Synced from Notion at ${new Date().toLocaleString()}*
`;

  await writeFile(localPath, markdown);

  // Index for search
  await indexForSearch(localPath, content, metadata);
}
```

### 6. Confirmation

```
✓ Note saved to Notion

📝 "Tenant prefers email for maintenance requests"
📁 Database: Property Notes
🏷️  Tags: tenant-communication, preference, maintenance
🔗 Notion: https://notion.so/page-abc123
📄 Local: /knowledge/notion/tenant-email-preference.md

Related Content:
  • Email: "Maintenance Request - Unit 2B" (Jan 20, 2025)
  • Contact: John Doe (Tenant - Unit 2B)
  • Calendar: "Property Walkthrough" (Jan 25, 2025)

Auto-indexed for search: ✓

Next Actions:
[1] Open in Notion → Opens browser
[2] View local copy → Opens markdown file
[3] Add to project → Links to existing project
[4] Share with team → Generate share link
```

## Smart Features

### Auto-Categorization

```javascript
const detectContentType = (content) => {
  // Meeting notes
  if (content.match(/meeting|discussed|attendees|agenda/i)) {
    return 'meeting';
  }

  // Ideas
  if (content.match(/idea|brainstorm|concept|could we/i)) {
    return 'idea';
  }

  // Tasks
  if (content.match(/todo|task|need to|action item/i)) {
    return 'task';
  }

  // Reference
  if (content.match(/reference|documentation|link|resource/i)) {
    return 'reference';
  }

  // Default
  return 'note';
};
```

### Auto-Tagging

```javascript
const extractTags = (content) => {
  const tags = [];

  // Extract hashtags
  const hashtags = content.match(/#(\w+)/g);
  if (hashtags) {
    tags.push(...hashtags.map(tag => tag.slice(1)));
  }

  // Smart tag suggestions based on content
  if (content.match(/tenant|lease|rent/i)) tags.push('property-management');
  if (content.match(/client|customer/i)) tags.push('client-relations');
  if (content.match(/revenue|expense|financial/i)) tags.push('finance');
  if (content.match(/marketing|campaign/i)) tags.push('marketing');

  return [...new Set(tags)]; // Remove duplicates
};
```

### Related Content Discovery

```javascript
const findRelatedContent = async (content, metadata) => {
  const related = [];

  // Search emails for matching keywords
  const emails = await mcp.gmail.search({
    query: extractKeywords(content).join(' OR ')
  });
  related.push(...emails.slice(0, 3).map(e => ({
    type: 'email',
    title: e.subject,
    url: `https://mail.google.com/mail/u/0/#inbox/${e.id}`
  })));

  // Search calendar for matching events
  const events = await mcp.calendar.searchEvents({
    query: extractKeywords(content).join(' ')
  });
  related.push(...events.slice(0, 2).map(e => ({
    type: 'calendar',
    title: e.summary,
    url: e.htmlLink
  })));

  // Search existing Notion pages
  const pages = await mcp.notion.search({
    query: extractKeywords(content).join(' ')
  });
  related.push(...pages.slice(0, 3).map(p => ({
    type: 'notion',
    title: p.properties.Name.title[0].text.content,
    url: p.url
  })));

  return related;
};
```

## Database Mapping

### Default Databases

**Notes Database** (General quick notes)

- Properties: Name, Type, Tags, Created, Source, Context

**Projects Database** (Project-related notes)

- Properties: Name, Project, Status, Priority, Due Date, Owner

**Contacts Database** (People and relationship notes)

- Properties: Name, Person, Company, Relationship, Last Contact

**Knowledge Base Database** (Reference and documentation)

- Properties: Name, Category, Tags, Source, URL, Created

### Custom Databases

Add to context configuration:

```json
{
  "integrations": {
    "notion": {
      "database_ids": {
        "tenant_notes": "db-tenant-789",
        "property_docs": "db-property-012"
      }
    }
  }
}
```

## Integration with Other Commands

### With /google:email

Save important emails to Notion:

```bash
/google:email search "from:important-client@example.com"
# Then
/notion:save-note --from-email <email-id>
```

### With /meeting:notes

Auto-save meeting notes:

```bash
/meeting:notes "Team Standup"
# Automatically saved to Notion meetings database
```

### With /knowledge:capture

Bidirectional sync:

```bash
/knowledge:capture "Important research findings"
# Saved to both /knowledge/ and Notion
```

### With /workflow:meeting-complete

Automated workflow:

```bash
# At end of meeting, automatically:
# 1. Saves notes to Notion
# 2. Extracts action items → Trello
# 3. Links everything together
```

## Business Value

**Time Savings**:

- Note capture: 30 sec vs 2-3 min (manual Notion)
- Saves 5-10 min/day = **0.8-1.5 hours/week**

**Productivity Gains**:

- Never lose ideas or important information
- Automatic organization and tagging
- Instant search across all notes
- Bidirectional sync (Notion ↔ Local)

**Knowledge Management**:

- Build comprehensive knowledge base
- Link related information automatically
- Search across email, calendar, Notion, local files
- Context-aware organization

## Success Metrics

✅ Note capture time <2 seconds
✅ Auto-categorization accuracy >85%
✅ Related content links 3+ items per note
✅ 100% sync success to local knowledge base
✅ Search index updated within 5 seconds

## Security & Privacy

- Notion Integration Token (not full OAuth scope)
- Encrypted token storage
- Per-context database isolation
- Local markdown backups
- Audit logging

## Troubleshooting

### MCP Server Not Installed

```bash
Error: Notion MCP server not found

Solution:
/mcp:install notion --auth-type api-token
```

### Database Not Found

```bash
Error: Database "Property Notes" not found

Solution:
# List available databases
/notion:list-databases

# Add to context
/context:switch property-management --edit-notion-databases
```

### Sync Failed

```bash
Error: Failed to sync to local knowledge base

Solution:
# Check local path permissions
ls -la /knowledge/notion/

# Retry sync
/notion:save-note --retry-last-sync
```

## Advanced Options

### Batch Capture

```bash
# Capture multiple notes from file
/notion:save-note --batch /path/to/notes.txt --separator "---"
```

### Template-Based

```bash
# Use Notion template
/notion:save-note --template "Meeting Notes" --interactive
```

### Voice Capture

```bash
# Capture from voice note (requires transcription)
/notion:save-note --from-voice /path/to/recording.mp3
```

## Related Commands

- `/notion:project` - Create Notion projects
- `/knowledge:capture` - Local knowledge capture
- `/capture` - Universal quick capture (routes to best tool)
- `/find` - Universal search across all sources
- `/workflow:meeting-complete` - Meeting → Note → Task flow

## Notes

**First Use**: Initial setup requires creating Notion integration and sharing databases.

**Performance**: Note capture completes in <2 seconds via MCP.

**Offline**: Can save locally when offline, syncs to Notion when back online.

**Limits**: Notion API rate limit: 3 requests/second (rarely hit with normal usage).

---

*Never lose an idea again. Capture everything, find anything.*
