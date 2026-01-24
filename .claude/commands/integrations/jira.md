---
description: Jira integration - create tickets from code, update status from commits, link PRs to tickets
argument-hint: [--mode <create|update|link>] [--ticket <ticket-id>] [--auto]
model: claude-sonnet-4-5-20250929
allowed-tools: Task, Bash, Read, Write, Glob, Grep
---

Jira Integration: **${ARGUMENTS}**

## Jira Project Management Integration

**Automate Jira workflows** including ticket creation, status updates, and PR linking.

**Capabilities**:

- Create tickets from code comments (TODO, FIXME)
- Update ticket status from git commits
- Link pull requests to Jira tickets
- Sync sprint data
- Automated project tracking

Routes to **github-ops-expert** agent for Jira integration:

```javascript
await Task({
  subagent_type: 'github-ops-expert',
  description: 'Integrate Jira with development workflow',
  prompt: `Execute Jira integration

Mode: ${MODE || 'create'}
Ticket: ${TICKET || 'auto-detect from branch/commit'}
Auto Mode: ${AUTO ? 'Yes' : 'No'}

## 1. Setup Jira API

\`\`\`bash
# Install Jira client
npm install --save-dev jira-client

# Configure Jira
export JIRA_HOST=yourcompany.atlassian.net
export JIRA_EMAIL=your-email@company.com
export JIRA_API_TOKEN=your-jira-api-token
\`\`\`

## 2. ${MODE === 'create' || !MODE ? 'Create Tickets from Code' : ''}

Scan code for TODO/FIXME comments and create Jira tickets.

\`\`\`bash
# Find TODOs in codebase
grep -r "// TODO:" src/ --include="*.js" --include="*.ts"

# Create Jira tickets
for todo in $(grep -r "// TODO:" src/); do
  # Extract TODO text
  # Create Jira ticket
  jira create --project DEV --type Task --summary "$todo"
done
\`\`\`

## 3. ${MODE === 'update' ? 'Update Status from Commits' : ''}

Parse git commits for Jira ticket IDs and update status.

\`\`\`bash
# Commit message format: "DEV-123: Fix login bug"
git log --oneline | grep -o "DEV-[0-9]\\+" | while read ticket; do
  jira transition $ticket "In Progress"
done
\`\`\`

## 4. ${MODE === 'link' ? 'Link PRs to Tickets' : ''}

Automatically link GitHub PRs to Jira tickets.

\`\`\`bash
# Extract ticket ID from branch name
TICKET=$(git branch --show-current | grep -o "DEV-[0-9]\\+")

# Create PR and link to Jira
gh pr create --title "[${TICKET}] Feature implementation"

# Add PR link to Jira ticket
jira comment $TICKET "PR: $(gh pr view --json url -q .url)"
\`\`\`
  `
})
```

## Usage

```bash
# Create tickets from TODOs
/integrations/jira --mode create

# Update ticket status
/integrations/jira --mode update --ticket DEV-123

# Link current PR to ticket
/integrations/jira --mode link --ticket DEV-123

# Auto mode (detect ticket from branch)
/integrations/jira --mode link --auto
```

## ROI

**Savings**: $10,000/year

- 3 hours/week saved on manual ticket updates
- Better project visibility
- Reduced context switching

---

**Setup**: Requires Jira API token
**Next**: `/integrations/figma`, `/integrations/notion`
