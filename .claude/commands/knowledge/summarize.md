---
description: Summarize recent project changes, decisions, and work
argument-hint: [--since <date>] [--save] [--format md|json|html]
model: claude-sonnet-4-5-20250929
allowed-tools: [Bash, Read, Grep, mcp__plugin_serena_serena__list_memories]
---

# /knowledge:summarize

Summarize changes: **${ARGUMENTS:-last 7 days}**

---

## Step 1: Parse Arguments and Determine Time Range

Extract time period and output format:

<commentary>
Default time range: last 7 days
Support common formats: 7d, 30d, 90d, since YYYY-MM-DD
</commentary>

1. Parse `--since` flag:
   - If date provided: Use as start date
   - If duration (e.g., "7d", "30d"): Calculate start date
   - If no flag: Default to 7 days ago

2. Parse `--format` flag:
   - `md`: Markdown (default)
   - `json`: Structured JSON
   - `html`: HTML report

3. Parse `--save` flag:
   - If set: Save to `docs/changelogs/`
   - If not set: Display only

Calculate date range:

```bash
# Default to 7 days ago
if [ -z "$SINCE_DATE" ]; then
  SINCE_DATE=$(date -d '7 days ago' +%Y-%m-%d)
fi

echo "📅 Summarizing changes since: $SINCE_DATE"
```

---

## Step 2: Gather Git Commit Data

Collect all commits since the start date:

```bash
# Get commit history since date
git log --since="$SINCE_DATE" --all --pretty=format:"%H|%an|%ae|%ad|%s" --date=short > /tmp/commits.txt

# Get detailed commit info (with stats)
git log --since="$SINCE_DATE" --all --stat --pretty=format:"%H|%an|%ae|%ad|%s" > /tmp/commits-detailed.txt

# Get commit count
COMMIT_COUNT=$(git log --since="$SINCE_DATE" --all --oneline | wc -l)

echo "📝 Found $COMMIT_COUNT commits"
```

Parse commit data:

```
Commits data structure:
- Hash
- Author name
- Author email
- Date
- Subject (first line of message)
- Files changed
- Lines added/removed
```

---

## Step 3: Categorize Commits

Group commits by type based on conventional commit messages:

<commentary>
Conventional commit prefixes:
- feat: New features
- fix: Bug fixes
- refactor: Code refactoring
- docs: Documentation updates
- chore: Maintenance tasks
- style: Code style changes
- test: Test additions/updates
- perf: Performance improvements
- ci: CI/CD changes
- build: Build system changes
</commentary>

Parse commit messages and categorize:

```bash
# Extract commit types
grep "^feat:" /tmp/commits.txt > /tmp/features.txt
grep "^fix:" /tmp/commits.txt > /tmp/fixes.txt
grep "^refactor:" /tmp/commits.txt > /tmp/refactoring.txt
grep "^docs:" /tmp/commits.txt > /tmp/docs.txt
grep "^chore:" /tmp/commits.txt > /tmp/chores.txt

# Count each category
FEATURE_COUNT=$(wc -l < /tmp/features.txt)
FIX_COUNT=$(wc -l < /tmp/fixes.txt)
REFACTOR_COUNT=$(wc -l < /tmp/refactoring.txt)
DOCS_COUNT=$(wc -l < /tmp/docs.txt)
CHORE_COUNT=$(wc -l < /tmp/chores.txt)
```

---

## Step 4: Gather Updated Serena Memories

Find memory files modified since start date:

Use `list_memories` to get all memories, then check modification times:

```bash
# Find modified memory files
find .claude/memories -name "*.md" -newermt "$SINCE_DATE" -type f > /tmp/updated-memories.txt

MEMORY_UPDATE_COUNT=$(wc -l < /tmp/updated-memories.txt)

echo "🧠 Updated $MEMORY_UPDATE_COUNT Serena memories"
```

For each updated memory:

1. Read the memory file
2. Extract recent changes (if timestamps in file)
3. Summarize what was added/changed

---

## Step 5: Gather Documentation Changes

Find modified documentation files:

```bash
# Find documentation files modified since date
find . -name "*.md" -not -path "*/node_modules/*" -not -path "*/.git/*" \
  -newermt "$SINCE_DATE" -type f > /tmp/doc-changes.txt

# Exclude memory files (already counted)
grep -v ".claude/memories" /tmp/doc-changes.txt > /tmp/doc-changes-filtered.txt

DOC_CHANGE_COUNT=$(wc -l < /tmp/doc-changes-filtered.txt)

echo "📚 Updated $DOC_CHANGE_COUNT documentation files"
```

Key documentation areas:

- README.md
- docs/**/*.md
- CLAUDE.md
- API documentation
- Guides and tutorials

---

## Step 6: Gather Dependency Updates

Check for dependency changes:

```bash
# Check if package.json changed
if git diff "$SINCE_DATE" --name-only | grep -q "package.json"; then
  echo "📦 Dependencies updated"

  # Get dependency changes
  git diff "$SINCE_DATE" package.json > /tmp/package-diff.txt

  # Parse added/removed/updated packages
  # Extract package names and versions
fi
```

Categorize dependency changes:

- Added dependencies
- Updated dependencies (patch, minor, major)
- Removed dependencies
- Security fixes

---

## Step 7: Check for Closed Issues/PRs

If GitHub CLI is available, fetch closed issues and PRs:

```bash
# Check if gh CLI is installed
if command -v gh &> /dev/null; then
  # Get closed issues since date
  gh issue list --state closed --search "closed:>=$SINCE_DATE" --json number,title,closedAt --limit 100 > /tmp/closed-issues.json

  # Get merged PRs since date
  gh pr list --state merged --search "merged:>=$SINCE_DATE" --json number,title,mergedAt --limit 100 > /tmp/merged-prs.json

  CLOSED_ISSUES=$(jq length /tmp/closed-issues.json)
  MERGED_PRS=$(jq length /tmp/merged-prs.json)

  echo "🎯 Closed $CLOSED_ISSUES issues, merged $MERGED_PRS PRs"
else
  echo "ℹ️  GitHub CLI not available - skipping issue/PR data"
fi
```

---

## Step 8: Extract Key Decisions and Rationale

Search for architectural decisions and important choices:

<commentary>
Look for decision keywords in commit messages and memory updates:
- "decided to", "chosen", "selected"
- "because", "due to", "in order to"
- "trade-off", "alternative", "considered"
</commentary>

Parse commit messages for decision indicators:

```bash
# Find decision-related commits
grep -iE "(decided|chose|selected|migrated)" /tmp/commits.txt > /tmp/decisions.txt
```

Extract from updated memories:

- Read each updated memory
- Look for decision sections (ADR format)
- Extract key decisions made

---

## Step 9: Calculate Summary Metrics

Generate aggregate statistics:

```bash
# File change statistics
TOTAL_FILES_CHANGED=$(git diff --name-only "$SINCE_DATE" | wc -l)
LINES_ADDED=$(git diff --shortstat "$SINCE_DATE" | grep -oP '\d+(?= insertion)' || echo "0")
LINES_REMOVED=$(git diff --shortstat "$SINCE_DATE" | grep -oP '\d+(?= deletion)' || echo "0")

# Active contributors
CONTRIBUTORS=$(git log --since="$SINCE_DATE" --format='%an' | sort -u | wc -l)

# Most active files
git log --since="$SINCE_DATE" --name-only --pretty=format: | \
  sort | uniq -c | sort -rn | head -10 > /tmp/active-files.txt
```

Metrics to calculate:

- Total commits
- Total files changed
- Lines added/removed
- Number of contributors
- Commit frequency (commits/day)
- Feature velocity (features/week)
- Bug fix rate (fixes/week)

---

## Step 10: Generate Summary Report

Create comprehensive summary in requested format:

### Markdown Format (Default)

```markdown
# Project Summary
**Period**: ${startDate} to ${endDate} (${daysCount} days)
**Generated**: ${timestamp}

---

## 📊 Overview

- **Total Commits**: ${totalCommits}
- **Contributors**: ${contributorCount}
- **Files Changed**: ${filesChanged}
- **Lines Added**: +${linesAdded}
- **Lines Removed**: -${linesRemoved}
- **Closed Issues**: ${closedIssues}
- **Merged PRs**: ${mergedPRs}

### Commit Frequency
${commitsPerDay} commits/day average

---

## 🚀 Features Added (${featureCount})

${featureCommits.map(c => `
### ${c.title}
- **Author**: ${c.author}
- **Date**: ${c.date}
- **Description**: ${c.description}
- **Files**: ${c.filesChanged}

${c.details}
`).join('\n')}

---

## 🐛 Bugs Fixed (${fixCount})

${bugFixes.map(f => `
- **${f.title}** (${f.date})
  - ${f.description}
  - Fixed by: ${f.author}
`).join('\n')}

---

## 🔧 Refactoring & Improvements (${refactorCount})

${refactorCommits.map(r => `
- **${r.title}** (${r.date})
  - ${r.description}
`).join('\n')}

---

## 📚 Documentation Updates (${docsCount})

${docUpdates.map(d => `
- **${d.file}** (${d.date})
  - ${d.description}
`).join('\n')}

---

## 🧠 Knowledge Base Updates

### Updated Serena Memories (${memoryUpdateCount})

${updatedMemories.map(m => `
#### ${m.name}
- **Last Modified**: ${m.date}
- **Changes**: ${m.summary}
- **Topics Added**: ${m.newTopics.join(', ')}
`).join('\n')}

---

## 📦 Dependency Changes

### Added Dependencies (${addedDepsCount})
${addedDeps.map(d => `- ${d.name}@${d.version} - ${d.description}`).join('\n')}

### Updated Dependencies (${updatedDepsCount})
${updatedDeps.map(d => `- ${d.name}: ${d.from} → ${d.to} (${d.type})`).join('\n')}

### Removed Dependencies (${removedDepsCount})
${removedDeps.map(d => `- ${d.name}@${d.version}`).join('\n')}

### Security Fixes (${securityFixCount})
${securityFixes.map(f => `- ${f.name}: Fixed ${f.cve} (${f.severity})`).join('\n')}

---

## 🎯 Key Decisions Made

${keyDecisions.map(kd => `
### ${kd.title}
**Date**: ${kd.date}
**Context**: ${kd.context}

**Decision**: ${kd.decision}

**Rationale**: ${kd.rationale}

**Alternatives Considered**: ${kd.alternatives}

**Consequences**: ${kd.consequences}
`).join('\n')}

---

## 📈 Impact Metrics

- **Codebase Growth**: ${netLinesChange > 0 ? '+' : ''}${netLinesChange} lines
- **Test Coverage**: ${testCoverage}% ${coverageChange}
- **Code Quality**: ${codeQualityScore}/100
- **Technical Debt**: ${techDebtChange}

---

## 🔥 Most Active Areas

| File/Directory | Changes | Lines Modified |
|----------------|---------|----------------|
${activeFiles.map(f => `| ${f.path} | ${f.changes} | ${f.lines} |`).join('\n')}

---

## 👥 Contributor Activity

| Contributor | Commits | Files | Lines Added | Lines Removed |
|-------------|---------|-------|-------------|---------------|
${contributors.map(c => `| ${c.name} | ${c.commits} | ${c.files} | +${c.linesAdded} | -${c.linesRemoved} |`).join('\n')}

---

## 🔮 Next Steps

Based on recent activity, suggested next steps:

${nextSteps.map(step => `
### ${step.title}
${step.description}
**Priority**: ${step.priority}
**Estimated Effort**: ${step.effort}
`).join('\n')}

---

## 📋 Open Items

### Remaining Issues (${openIssuesCount})
${openIssues.map(i => `- #${i.number}: ${i.title}`).join('\n')}

### Open PRs (${openPRsCount})
${openPRs.map(pr => `- #${pr.number}: ${pr.title} (${pr.author})`).join('\n')}

---

**Report Generated**: ${timestamp}
**Next Summary**: ${nextSummaryDate}
```

### JSON Format

```json
{
  "period": {
    "start": "${startDate}",
    "end": "${endDate}",
    "days": ${daysCount}
  },
  "summary": {
    "commits": ${totalCommits},
    "contributors": ${contributorCount},
    "filesChanged": ${filesChanged},
    "linesAdded": ${linesAdded},
    "linesRemoved": ${linesRemoved},
    "closedIssues": ${closedIssues},
    "mergedPRs": ${mergedPRs}
  },
  "features": [
    ${features}
  ],
  "bugFixes": [
    ${bugFixes}
  ],
  "refactoring": [
    ${refactoring}
  ],
  "documentation": [
    ${documentation}
  ],
  "memories": [
    ${memoryUpdates}
  ],
  "dependencies": {
    "added": [${addedDeps}],
    "updated": [${updatedDeps}],
    "removed": [${removedDeps}],
    "security": [${securityFixes}]
  },
  "decisions": [
    ${decisions}
  ],
  "metrics": {
    "codebaseGrowth": ${netLinesChange},
    "testCoverage": ${testCoverage},
    "codeQuality": ${codeQualityScore},
    "techDebt": ${techDebtScore}
  }
}
```

---

## Step 11: Save Report (if --save flag)

If `--save` flag is set, save to docs/changelogs/:

```bash
# Create changelogs directory if it doesn't exist
mkdir -p docs/changelogs

# Generate filename
FILENAME="docs/changelogs/summary-${startDate}-to-${endDate}.${format}"

# Save report
cat /tmp/summary-report.${format} > "$FILENAME"

echo "💾 Report saved to: $FILENAME"
```

Optionally commit the changelog:

```bash
git add "$FILENAME"
git commit -m "docs: add changelog for ${startDate} to ${endDate}

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Step 12: Display Summary

Show the generated summary to user:

If format is markdown, display with formatting.
If format is JSON, display formatted JSON.
If format is HTML, save to file and offer to open in browser.

---

## Step 13: Offer Follow-Up Actions

Suggest related commands:

```
📌 Follow-Up Actions:

1. **Update Knowledge Base**
   Capture key decisions: /knowledge:update-memory

2. **Share with Team**
   ${saveEnabled ? `Changelog saved to: ${filename}` : 'Save with: /knowledge:summarize --save'}

3. **Review Metrics**
   Check detailed analytics: /analytics:command-usage

4. **Plan Next Sprint**
   Review open items and create plan

5. **Generate Report for Stakeholders**
   Export as HTML: /knowledge:summarize --since ${startDate} --format html
```

---

## Example Usage

### Last 7 days (default)

```bash
/knowledge:summarize
```

### Last 30 days

```bash
/knowledge:summarize --since 30d
```

### Since specific date

```bash
/knowledge:summarize --since 2025-01-01
```

### Save to changelog

```bash
/knowledge:summarize --save
```

### JSON format

```bash
/knowledge:summarize --since 30d --format json --save
```

### HTML report

```bash
/knowledge:summarize --since 90d --format html --save
```

---

## Advanced Features

### Compare Periods

If user wants to compare two periods:

```
Would you like to compare with a previous period?

Options:
1. Previous ${daysCount} days
2. Same period last month
3. Same period last quarter
4. Custom period

Comparing periods shows:
- Commit velocity change
- Feature velocity change
- Bug fix rate change
- Code quality trends
- Team productivity trends
```

### Auto-Generate Release Notes

Extract feature commits and format as release notes:

```
Generate release notes for version ${version}?

This will create a RELEASE_NOTES.md with:
- Version number
- Release date
- New features
- Bug fixes
- Breaking changes
- Upgrade instructions
```

---

**Command Complete** 📊
