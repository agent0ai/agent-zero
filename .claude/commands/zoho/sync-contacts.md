---
description: Sync contacts between Zoho CRM and other systems
argument-hint: <source> <target> [--direction one-way|two-way] [--conflict-resolution source|target|manual] [--dry-run]
model: claude-sonnet-4-5-20250929
allowed-tools: [Bash, Read, Write, AskUserQuestion, Task]
---

# /zoho:sync-contacts

Sync contacts: **$ARGUMENTS**

## Step 1: Parse Arguments

Determine:

- Source system (Zoho CRM, Gmail, LinkedIn, CSV)
- Target system
- Sync direction (one-way or two-way)
- Conflict resolution strategy

## Step 2: Fetch Source Contacts

```bash
# Zoho CRM
curl "https://www.zohoapis.com/crm/v2/Contacts" \
  -H "Authorization: Zoho-oauthtoken $ACCESS_TOKEN" > /tmp/zoho-contacts.json

# Gmail Contacts
curl "https://people.googleapis.com/v1/people/me/connections" \
  -H "Authorization: Bearer $GMAIL_TOKEN" > /tmp/gmail-contacts.json
```

## Step 3: Fetch Target Contacts

Similarly fetch from target system.

## Step 4: Detect Changes

Compare contacts:

```javascript
const changes = {
  new: sourceContacts.filter(s => !targetContacts.find(t => t.email === s.email)),
  updated: sourceContacts.filter(s => {
    const target = targetContacts.find(t => t.email === s.email);
    return target && isModified(s, target);
  }),
  deleted: targetContacts.filter(t => !sourceContacts.find(s => s.email === t.email))
};
```

## Step 5: Show Preview

```markdown
# 📋 Sync Preview

## Changes to Apply

### New Contacts (${changes.new.length})
${changes.new.slice(0, 5).map(c => `- ${c.name} <${c.email}>`).join('\n')}
${changes.new.length > 5 ? `... and ${changes.new.length - 5} more` : ''}

### Updated Contacts (${changes.updated.length})
${changes.updated.slice(0, 5).map(c => `- ${c.name}: ${c.changes}`).join('\n')}

### Conflicts (${conflicts.length})
${conflicts.map(c => `- ${c.name}: Modified in both systems`).join('\n')}

**Total Operations**: ${operationCount}

Continue? (y/n)
```

## Step 6: Handle Conflicts

For each conflict, ask user:

```
Conflict: ${contact.name} <${contact.email}>

Source: ${source.lastModified} - ${source.changes}
Target: ${target.lastModified} - ${target.changes}

Resolution:
1. Keep source version
2. Keep target version
3. Merge (keep both changes)
4. Skip this contact
```

## Step 7: Apply Changes

With approval workflow:

```javascript
for (const contact of changes.new) {
  console.log(`Creating: ${contact.name}`);
  await createContact(target, contact);
}

for (const contact of changes.updated) {
  console.log(`Updating: ${contact.name}`);
  await updateContact(target, contact);
}
```

## Step 8: Generate Sync Report

```markdown
# ✅ Contact Sync Complete

## Summary
- Created: ${createdCount} contacts
- Updated: ${updatedCount} contacts
- Deleted: ${deletedCount} contacts
- Conflicts resolved: ${conflictsCount}
- Errors: ${errorCount}

## Details
${syncLog}

Sync log saved to: sync-${timestamp}.log
```

**Command Complete** 🔄
