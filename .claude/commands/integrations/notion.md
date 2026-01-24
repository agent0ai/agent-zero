---
description: Notion integration - sync documentation, update changelogs, create project pages
argument-hint: [--mode <sync-docs|changelog|create-page>] [--page <notion-page-id>] [--auto]
model: claude-sonnet-4-5-20250929
allowed-tools: Task, Bash, Read, Write, Glob
---

Notion Integration: **${ARGUMENTS}**

## Notion Documentation Synchronization

**Automate Notion workflows** including documentation sync, changelog updates, and project page creation.

**Capabilities**:

- Sync markdown docs to Notion
- Auto-update changelogs from git commits
- Create project pages from templates
- Sync README files
- Automated documentation workflow

Routes to **documentation-expert-agent** for Notion sync:

```javascript
await Task({
  subagent_type: 'documentation-expert-agent',
  description: 'Sync documentation to Notion',
  prompt: `Execute Notion integration

Mode: ${MODE || 'sync-docs'}
Page: ${PAGE || 'auto-detect from notion.config.json'}
Auto Mode: ${AUTO ? 'Yes' : 'No'}

## 1. Setup Notion API

\`\`\`bash
# Install Notion client
npm install --save-dev @notionhq/client

# Configure Notion
export NOTION_TOKEN=your-notion-integration-token
export NOTION_DATABASE_ID=your-database-id
\`\`\`

## 2. ${MODE === 'sync-docs' || !MODE ? 'Sync Documentation' : ''}

Sync markdown files to Notion pages.

\`\`\`javascript
const { Client } = require('@notionhq/client');
const notion = new Client({ auth: process.env.NOTION_TOKEN });

// Convert markdown to Notion blocks
const blocks = markdownToNotionBlocks(markdownContent);

// Update Notion page
await notion.pages.update({
  page_id: pageId,
  children: blocks
});
\`\`\`

## 3. ${MODE === 'changelog' ? 'Update Changelog' : ''}

Generate changelog from git commits and update Notion.

\`\`\`bash
# Generate changelog
git log --oneline --since="1 week ago" > CHANGELOG.md

# Convert to Notion format and update
node scripts/update-notion-changelog.js
\`\`\`

## 4. ${MODE === 'create-page' ? 'Create Project Page' : ''}

Create new project page from template.

\`\`\`javascript
await notion.pages.create({
  parent: { database_id: process.env.NOTION_DATABASE_ID },
  properties: {
    Name: { title: [{ text: { content: "New Project" } }] },
    Status: { select: { name: "In Progress" } }
  }
});
\`\`\`
  `
})
```

## Usage

```bash
# Sync all markdown docs
/integrations/notion --mode sync-docs

# Update changelog
/integrations/notion --mode changelog

# Create new project page
/integrations/notion --mode create-page

# Auto-sync (detect changes)
/integrations/notion --mode sync-docs --auto
```

## ROI

**Savings**: $10,000/year

- 7 hours/week saved on manual documentation
- Up-to-date docs automatically
- Better knowledge sharing

---

**Setup**: Requires Notion API token
**Next**: `/integrations/figma`, `/integrations/jira`
