---
description: Sync GitHub issues to project management tools (Notion, Trello)
argument-hint: <target> [--filter open|assigned|label:<label>] [--direction one-way|two-way]
model: claude-haiku-4-20250528
allowed-tools: [Bash, Read, Write, AskUserQuestion]
---

# /github:sync-issues

Sync issues to: **$ARGUMENTS**

## Step 1: Fetch GitHub Issues

```bash
gh issue list --state open --json number,title,body,labels,assignees,milestone,createdAt \
  --limit 100 > /tmp/github-issues.json
```

## Step 2: Fetch Target Items

**Notion**:

```bash
curl -X POST "https://api.notion.com/v1/databases/$DB_ID/query" \
  -H "Authorization: Bearer $NOTION_TOKEN" > /tmp/notion-items.json
```

**Trello**:

```bash
curl "https://api.trello.com/1/boards/$BOARD_ID/cards?key=$KEY&token=$TOKEN" \
  > /tmp/trello-cards.json
```

## Step 3: Map Issues to Items

```javascript
const mapping = githubIssues.map(issue => {
  const existingItem = targetItems.find(item =>
    item.metadata?.githubIssue === issue.number
  );

  return {
    githubIssue: issue,
    targetItem: existingItem,
    action: existingItem ? 'update' : 'create'
  };
});
```

## Step 4: Show Preview

```markdown
# 🔄 Sync Preview

## To Create (${createCount})
${toCreate.map(i => `- #${i.number}: ${i.title}`).join('\n')}

## To Update (${updateCount})
${toUpdate.map(i => `- #${i.number}: ${i.title} (${i.changes})`).join('\n')}

Continue? (y/n)
```

## Step 5: Execute Sync

```javascript
for (const item of mapping) {
  if (item.action === 'create') {
    await createTargetItem({
      title: item.githubIssue.title,
      description: item.githubIssue.body,
      labels: item.githubIssue.labels.map(l => l.name),
      metadata: { githubIssue: item.githubIssue.number }
    });
  } else if (item.action === 'update') {
    await updateTargetItem(item.targetItem.id, {
      title: item.githubIssue.title,
      description: item.githubIssue.body
    });
  }
}
```

## Step 6: Summary

```markdown
# ✅ Sync Complete

- Created: ${createdCount} items
- Updated: ${updatedCount} items
- Errors: ${errorCount}

Next sync: Run `/github:sync-issues ${target}` again
```

**Command Complete** 🔄
