---
description: Universal search across Gmail, Calendar, Notion, Trello, Drive, and local KB - one search, all results
argument-hint: "<query> [--source <gmail|calendar|notion|trello|drive|local|all>] [--limit <num>]"
model: claude-3-5-sonnet-20241022
allowed-tools:
  - Bash
  - Read
  - Grep
  - Write
---

# Universal Search Command

## Overview

**ONE SEARCH TO FIND EVERYTHING**

Search across all your productivity tools simultaneously. Returns ranked, unified results from Gmail, Google Calendar, Notion, Trello, Google Drive, and local knowledge base.

**Part of Phase 2**: Unified productivity integration

## What This Command Does

- ✅ Searches 6+ sources in parallel (<2 seconds)
- ✅ AI-powered relevance ranking
- ✅ Context-aware results
- ✅ Unified result format
- ✅ Direct links to open anywhere
- ✅ **Find anything in <2 seconds**

## Usage

```bash
# Search everything
/find "tenant email preference"

# Search specific source
/find "budget 2025" --source notion

# Limit results
/find "client meeting" --limit 10

# Search by date range
/find "property maintenance" --after "2025-01-01"

# Search by type
/find "lease" --type file

# Advanced query
/find "from:client@acme.com project deadline"
```

## Search Sources

| Source | What It Searches | Speed |
|--------|------------------|-------|
| **Gmail** | Emails (subject, body, attachments) | <500ms |
| **Calendar** | Events (title, description, location) | <300ms |
| **Notion** | Pages, databases, blocks | <800ms |
| **Trello** | Cards, boards, checklists, comments | <600ms |
| **Drive** | Files, folders, documents | <700ms |
| **Local KB** | Markdown files, notes | <200ms |

**Total**: All sources searched in parallel in <2 seconds

## Step-by-Step Execution

### 1. Parse Query

```javascript
// Parse search query and extract metadata
const query = parseQuery(searchString);

const searchParams = {
  keywords: query.keywords,
  filters: {
    source: options.source || 'all',
    dateRange: {
      after: options.after || null,
      before: options.before || null
    },
    type: options.type || null, // email, event, note, task, file
    context: getCurrentContext().name
  },
  limit: options.limit || 20
};
```

### 2. Execute Parallel Search

```javascript
// Search all sources in parallel
const searchPromises = [];

if (searchParams.filters.source === 'all' || searchParams.filters.source === 'gmail') {
  searchPromises.push(
    mcp.gmail.search({
      query: buildGmailQuery(searchParams),
      maxResults: searchParams.limit
    }).then(results => results.map(r => ({
      source: 'gmail',
      type: 'email',
      title: r.subject,
      snippet: r.snippet,
      date: r.date,
      url: `https://mail.google.com/mail/u/0/#inbox/${r.id}`,
      metadata: {
        from: r.from,
        to: r.to,
        hasAttachments: r.hasAttachments
      }
    })))
  );
}

if (searchParams.filters.source === 'all' || searchParams.filters.source === 'calendar') {
  searchPromises.push(
    mcp.calendar.searchEvents({
      query: searchParams.keywords.join(' '),
      timeMin: searchParams.filters.dateRange.after,
      timeMax: searchParams.filters.dateRange.before
    }).then(results => results.map(r => ({
      source: 'calendar',
      type: 'event',
      title: r.summary,
      snippet: r.description?.substring(0, 200),
      date: r.start.dateTime || r.start.date,
      url: r.htmlLink,
      metadata: {
        start: r.start,
        end: r.end,
        attendees: r.attendees?.length || 0
      }
    })))
  );
}

if (searchParams.filters.source === 'all' || searchParams.filters.source === 'notion') {
  searchPromises.push(
    mcp.notion.search({
      query: searchParams.keywords.join(' '),
      filter: {
        property: 'object',
        value: 'page'
      }
    }).then(results => results.map(r => ({
      source: 'notion',
      type: getNotionPageType(r),
      title: r.properties.Name?.title[0]?.text.content || 'Untitled',
      snippet: extractNotionSnippet(r),
      date: r.created_time,
      url: r.url,
      metadata: {
        database: r.parent.database_id,
        lastEdited: r.last_edited_time
      }
    })))
  );
}

if (searchParams.filters.source === 'all' || searchParams.filters.source === 'trello') {
  searchPromises.push(
    mcp.trello.search({
      query: searchParams.keywords.join(' '),
      modelTypes: 'cards',
      cards_limit: searchParams.limit
    }).then(results => results.map(r => ({
      source: 'trello',
      type: 'task',
      title: r.name,
      snippet: r.desc.substring(0, 200),
      date: r.dateLastActivity,
      url: r.shortUrl,
      metadata: {
        board: r.board.name,
        list: r.list.name,
        due: r.due,
        labels: r.labels.map(l => l.name)
      }
    })))
  );
}

if (searchParams.filters.source === 'all' || searchParams.filters.source === 'drive') {
  searchPromises.push(
    mcp.drive.searchFiles({
      query: searchParams.keywords.join(' '),
      fields: 'files(id,name,mimeType,modifiedTime,webViewLink,owners,size)'
    }).then(results => results.map(r => ({
      source: 'drive',
      type: 'file',
      title: r.name,
      snippet: `${formatFileSize(r.size)} - ${r.mimeType}`,
      date: r.modifiedTime,
      url: r.webViewLink,
      metadata: {
        mimeType: r.mimeType,
        owner: r.owners[0].displayName,
        size: r.size
      }
    })))
  );
}

if (searchParams.filters.source === 'all' || searchParams.filters.source === 'local') {
  searchPromises.push(
    searchLocalKB({
      keywords: searchParams.keywords,
      dateRange: searchParams.filters.dateRange
    }).then(results => results.map(r => ({
      source: 'local',
      type: 'note',
      title: r.title,
      snippet: r.snippet,
      date: r.modified,
      url: `file://${r.path}`,
      metadata: {
        path: r.path,
        wordCount: r.wordCount,
        tags: r.tags
      }
    })))
  );
}

// Wait for all searches to complete
const allResults = (await Promise.all(searchPromises)).flat();
```

### 3. AI-Powered Ranking

```javascript
// Rank results by relevance using AI
const rankedResults = await claude.rank({
  prompt: `Rank these search results by relevance to the query.

  Query: "${searchParams.keywords.join(' ')}"
  User Context: ${searchParams.filters.context}
  Total Results: ${allResults.length}

  Results:
  ${allResults.map((r, i) => `
  [${i}] ${r.source} - ${r.type}
  Title: ${r.title}
  Snippet: ${r.snippet}
  Date: ${r.date}
  `).join('\n')}

  Rank by:
  1. Keyword match relevance
  2. Recency (newer is better)
  3. Source authority (email/calendar > notes)
  4. Context relevance

  Return array of indices in ranked order: [3, 7, 1, ...]
  `
});

const sortedResults = rankedResults.map(index => allResults[index]);
```

### 4. Format and Display

```
╔════════════════════════════════════════════════════════════════╗
║  🔍 SEARCH RESULTS FOR: "tenant email preference"             ║
╠════════════════════════════════════════════════════════════════╣
║  Found 12 results across 4 sources (searched in 1.8 seconds)  ║
╠════════════════════════════════════════════════════════════════╣

[1] 📧 Gmail - Email
    "Maintenance Request - Unit 2B Tenant Communication"
    From: john.doe@tenant.com | Jan 20, 2025
    Tenant prefers email for all maintenance requests...
    🔗 https://mail.google.com/mail/u/0/#inbox/abc123

[2] 📝 Notion - Note
    "Tenant prefers email for maintenance requests"
    Property Notes database | Jan 21, 2025
    Note captured from conversation with Unit 2B tenant...
    🔗 https://notion.so/page-xyz789

[3] 💾 Local KB - Note
    "tenant-email-preference.md"
    /knowledge/captured/ | Jan 21, 2025
    Auto-saved from /capture command. Tags: #tenant-communication
    🔗 file:///knowledge/captured/tenant-email-preference.md

[4] 📧 Gmail - Email
    "Re: Communication Preferences for Maintenance"
    From: property-manager@company.com | Jan 19, 2025
    Following up on tenant preferences for maintenance...
    🔗 https://mail.google.com/mail/u/0/#inbox/def456

[5] 📋 Trello - Task
    "Update tenant communication preferences in CRM"
    Property Management board | Jan 21, 2025
    Update Zoho CRM with tenant email preference for maintenance
    🔗 https://trello.com/c/ghi789

[6] 📅 Calendar - Event
    "Property Walkthrough - Unit 2B"
    Jan 25, 2025 2:00 PM
    Discuss maintenance process and communication preferences
    🔗 https://calendar.google.com/event/jkl012

[7] 📝 Notion - Task
    "Document tenant communication preferences"
    Tasks database | Jan 21, 2025
    Status: To Do | Priority: Medium | Due: Jan 25
    🔗 https://notion.so/task-mno345

[8] 💾 Local KB - Note
    "unit-2b-tenant-communication-log.md"
    /knowledge/properties/123-main-st/ | Jan 18, 2025
    Communication log for Unit 2B tenant interactions...
    🔗 file:///knowledge/properties/123-main-st/unit-2b.md

╠════════════════════════════════════════════════════════════════╣
║  📊 RESULTS BY SOURCE                                          ║
║    Gmail: 4 emails                                             ║
║    Notion: 2 pages                                             ║
║    Local KB: 2 notes                                           ║
║    Trello: 1 card                                              ║
║    Calendar: 1 event                                           ║
║                                                                ║
║  🏷️  COMMON TAGS: tenant-communication, maintenance, unit-2b  ║
║                                                                ║
║  📅 DATE RANGE: Jan 18 - Jan 21, 2025 (4 days)                ║
╚════════════════════════════════════════════════════════════════╝

Quick Actions:
[1-8] Open result → Opens in default app
[a] Open all in browser → Opens top 5 results
[c] Copy links → Copies all URLs to clipboard
[f] Filter by source → Refine search
[r] Related search → "tenant communication preferences"
```

## Advanced Search Syntax

### Gmail-Style Operators

```bash
# From specific person
/find "from:client@acme.com budget"

# Specific subject
/find "subject:lease agreement"

# With attachments
/find "has:attachment contract"

# Date ranges
/find "after:2025-01-01 before:2025-02-01 invoice"
```

### Type Filters

```bash
# Emails only
/find "project update" --type email

# Tasks only
/find "maintenance" --type task

# Files only
/find "contract" --type file

# Events only
/find "client meeting" --type event
```

### Source-Specific Search

```bash
# Search only Gmail
/find "budget report" --source gmail

# Search only Notion
/find "project notes" --source notion

# Search only Trello
/find "urgent tasks" --source trello
```

## Integration with Other Commands

### With /capture

Everything captured is searchable:

```bash
/capture "Important client feedback"
# Later...
/find "client feedback"
# → Returns captured note from all sources
```

### With /workflow:email-to-task

Tasks created from emails are linked:

```bash
# Email converted to task
/workflow:email-to-task --email-id msg_123
# Later...
/find "client deadline"
# → Returns email, Trello card, Notion task, Calendar event
```

### With /knowledge:capture

Local knowledge base integration:

```bash
/knowledge:capture "Research findings"
# Later...
/find "research"
# → Searches local KB along with all other sources
```

## Business Value

**Time Savings**:

- Manual search across tools: 5-10 minutes
- Universal search: <2 seconds
- **Saves 5-10 min per search = 1-2 hours/week**

**Productivity Gains**:

- Never lose information again
- One search instead of 6
- AI-ranked results (best first)
- Context-aware (shows what matters to you)

**Knowledge Management**:

- Everything indexed and searchable
- Cross-referenced automatically
- Find relationships between items
- Historical context preserved

## Success Metrics

✅ Search completes in <2 seconds
✅ Relevance ranking accuracy >85%
✅ Results from all sources >95%
✅ User finds what they need >90% of time
✅ User satisfaction >8/10

## Security & Privacy

- Search queries not stored
- Results filtered by context (only your data)
- OAuth 2.0 for all tool access
- Local KB searches stay local

## Troubleshooting

### No Results Found

```bash
# Try broader search
/find "maintenance" instead of "tenant email preference maintenance communication"

# Check which sources are enabled
/mcp:list --test-connections

# Try specific source
/find "query" --source gmail
```

### Too Many Results

```bash
# Use filters
/find "meeting" --after "2025-01-15" --type event

# Limit results
/find "client" --limit 5

# Use specific source
/find "client" --source notion
```

### Wrong Results Ranked First

```bash
# Provide more specific query
/find "Unit 2B tenant email preference" instead of "email"

# Use operators
/find "from:tenant@example.com preference"
```

## Advanced Features

### Saved Searches

```bash
# Save frequently used searches
/find "urgent tasks" --save-as "my-urgent-tasks"

# Run saved search
/find --saved "my-urgent-tasks"
```

### Search Alerts

```bash
# Get notified of new results
/find "client deadline" --alert daily
# → Email digest of new matches
```

### Export Results

```bash
# Export to CSV
/find "2025 Q1 projects" --export csv

# Export to markdown
/find "client meetings" --export md
```

## Related Commands

- `/capture` - Universal quick capture
- `/knowledge:capture` - Local knowledge base
- `/google:email search` - Gmail-specific search
- `/notion:save-note` - Notion capture
- `/trello:card list` - Trello card listing

## Notes

**First Use**: Requires at least one integration (Gmail, Notion, Trello, or Drive) configured.

**Performance**: Parallel search completes in <2 seconds across all sources.

**Indexing**: New content indexed automatically within 5 seconds of creation.

**Offline**: Local KB search works offline; cloud sources require internet.

---

*One search to find everything. Stop searching for where you saved something.*
