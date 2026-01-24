---
description: Create pull request with AI-generated description and comprehensive checklist
argument-hint: [--draft] [--base <branch>]
allowed-tools: Task, Bash, AskUserQuestion
model: claude-sonnet-4-5
timeout: 900
retry: 2
cost_estimate: 0.15-0.25

validation:
  input:
    base_branch:
      required: false
      default: "main"
      error_message: "Base branch must be a valid git branch"
  output:
    schema: .claude/validation/schemas/dev/create-pr-output.json
    required_files:
      - 'pull-requests/pr-${pr_number}-report.json'
    min_file_size: 300
    quality_threshold: 0.90
    content_requirements:
      - "PR created successfully"
      - "PR number assigned"
      - "Description generated with AI"
      - "Reviewers requested"
      - "CI/CD triggered"

version: 2.0.0
changelog:
  - version: 2.0.0
    date: 2026-01-20
    changes:
      - "Migrated to modern pattern with comprehensive validation"
      - "Added output validation for PR creation"
      - "Streamlined from 537 lines to focused workflow"
      - "Enhanced AI description generation with context analysis"
      - "Safety checks for branch validation"
  - version: 1.0.0
    date: 2025-08-10
    changes:
      - "Initial implementation with GitHub CLI integration"
---

# Create Pull Request

Arguments: **$ARGUMENTS**

## Step 1: Validate Input & Prerequisites

```bash
ARGS="$ARGUMENTS"
IS_DRAFT=$(echo "$ARGS" | grep -q '\-\-draft' && echo "true" || echo "false")
BASE_BRANCH=$(echo "$ARGS" | grep -oP '\-\-base\s+\K\S+' || echo "main")

# Check not on main branch
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" = "main" ] || [ "$CURRENT_BRANCH" = "master" ]; then
  echo "❌ ERROR: Cannot create PR from main branch"
  echo "You are currently on: $CURRENT_BRANCH"
  exit 1
fi

# Check branch is pushed to remote
if ! git rev-parse --abbrev-ref --symbolic-full-name @{u} 2>/dev/null; then
  echo "⚠️  Branch not pushed to remote. Pushing now..."
  git push -u origin $CURRENT_BRANCH
fi

# Check for uncommitted changes
if ! git diff-index --quiet HEAD --; then
  echo "⚠️  WARNING: Uncommitted changes detected"
  echo "Commit or stash changes before creating PR"
  exit 1
fi

echo "✓ Prerequisites validated"
echo "  Current branch: $CURRENT_BRANCH"
echo "  Base branch: $BASE_BRANCH"
echo "  Draft mode: $IS_DRAFT"
```

## Step 2: Gather PR Context

```bash
CURRENT_BRANCH="$CURRENT_BRANCH"
BASE_BRANCH="$BASE_BRANCH"

# Get commit history
echo "Analyzing branch changes..."
git log origin/$BASE_BRANCH..HEAD --oneline --no-merges > /tmp/pr-commits.txt

# Get changed files with stats
git diff --stat origin/$BASE_BRANCH...HEAD > /tmp/pr-stats.txt
git diff --name-only origin/$BASE_BRANCH...HEAD > /tmp/pr-files.txt

# Generate full diff for AI analysis
git diff origin/$BASE_BRANCH...HEAD > /tmp/pr-diff.txt

# Count changes
FILES_CHANGED=$(cat /tmp/pr-files.txt | wc -l)
COMMITS_COUNT=$(cat /tmp/pr-commits.txt | wc -l)

echo "✓ PR context gathered"
echo "  Files changed: $FILES_CHANGED"
echo "  Commits: $COMMITS_COUNT"
```

## Step 3: Generate PR Description Using AI

```javascript
const CURRENT_BRANCH = process.env.CURRENT_BRANCH;
const BASE_BRANCH = process.env.BASE_BRANCH || 'main';
const IS_DRAFT = process.env.IS_DRAFT === 'true';

// Read context files
const commits = await Bash({
  command: 'cat /tmp/pr-commits.txt',
  description: 'Read commit history'
});

const fileStats = await Bash({
  command: 'cat /tmp/pr-stats.txt',
  description: 'Read file statistics'
});

const diffSummary = await Bash({
  command: 'git diff --stat origin/' + BASE_BRANCH + '...HEAD',
  description: 'Get diff summary'
});

await Task({
  subagent_type: 'general-purpose',
  description: 'Generate PR description and details',
  prompt: `Generate a comprehensive pull request description for GitHub.

BRANCH CONTEXT:
Source: ${CURRENT_BRANCH}
Target: ${BASE_BRANCH}

COMMITS IN THIS BRANCH:
${commits.stdout}

FILE CHANGES:
${fileStats.stdout}

DETAILED DIFF STATS:
${diffSummary.stdout}

GENERATE PR CONTENT:

**1. PR Title**:
- Clear and concise (max 72 characters)
- Follow conventional commits format (feat:, fix:, refactor:, etc.)
- Include issue number if branch name contains it (e.g., feature/123-name → #123)
- Example: "feat: add user profile upload feature (#123)"

**2. PR Description** (comprehensive markdown):
## Summary
[1-2 sentence overview of what this PR does]

## Changes
- [Key change 1 with context]
- [Key change 2 with context]
- [Key change 3 with context]

## Type of Change
- [ ] Bug fix (non-breaking change fixing an issue)
- [ ] New feature (non-breaking change adding functionality)
- [ ] Breaking change (fix or feature causing existing functionality to change)
- [ ] Refactoring (no functional changes)
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Security fix

## Testing
- [ ] Unit tests pass locally
- [ ] Integration tests pass locally
- [ ] E2E tests pass (if applicable)
- [ ] Manual testing completed

**Test Coverage**: [estimate]% (target: 80%)

**Manual Testing Steps**:
1. [Step 1]
2. [Step 2]
3. [Step 3]

## Screenshots/Recordings
[If UI changes, note screenshots should be added]

## Performance Impact
- Bundle size: [increased/decreased/unchanged]
- Load time: [impact if measurable]
- API latency: [impact if measurable]

## Security Considerations
- [ ] No sensitive data exposed
- [ ] Input validation implemented
- [ ] Authorization checks in place
- [ ] No new security vulnerabilities introduced

## Database Migrations
- [ ] No migrations needed
- [ ] Migrations included and tested
- [ ] Migration rollback tested

## Dependencies
- [ ] No new dependencies
- [ ] New dependencies added: [list if any]
- [ ] Dependencies updated: [list if any]

## Documentation
- [ ] Code comments added/updated
- [ ] README updated (if needed)
- [ ] API docs updated (if needed)
- [ ] CHANGELOG entry added

## Deployment Notes
[Any special deployment considerations]

## Related Issues
Closes #[issue number if applicable]

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Tests added for new functionality
- [ ] All tests passing
- [ ] No console.log or debugging code left
- [ ] Documentation updated
- [ ] Branch is up to date with base branch

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)
Co-Authored-By: Claude <noreply@anthropic.com>

**3. Labels** (auto-detect based on files changed):
- Analyze file patterns to suggest labels (frontend, backend, feature, bugfix, etc.)

**4. Suggested Reviewers** (based on CODEOWNERS or file patterns):
- Suggest reviewers based on changed files
- Frontend changes → frontend-team
- Backend changes → backend-team
- Security-related → security-team

**5. Linked Issues**:
- Extract issue numbers from branch name or commits
- Format: Closes #123, Related to #456

Save PR details to: pull-requests/pr-draft.json
{
  "title": "...",
  "description": "...",
  "labels": ["feature", "frontend"],
  "suggested_reviewers": ["@alice", "@bob"],
  "linked_issues": [123]
}

Provide the generated PR title and description.`,

  context: {
    current_branch: CURRENT_BRANCH,
    base_branch: BASE_BRANCH,
    is_draft: IS_DRAFT,
    pr_draft_output: 'pull-requests/pr-draft.json'
  }
});
```

## Step 4: Preview & Approve PR

```bash
# Check PR draft created
if [ ! -f "pull-requests/pr-draft.json" ]; then
  echo "❌ ERROR: PR draft not created"
  exit 1
fi

# Display PR preview
PR_TITLE=$(jq -r '.title' pull-requests/pr-draft.json)
PR_DESCRIPTION=$(jq -r '.description' pull-requests/pr-draft.json)
LABELS=$(jq -r '.labels | join(", ")' pull-requests/pr-draft.json)
REVIEWERS=$(jq -r '.suggested_reviewers | join(", ")' pull-requests/pr-draft.json)

echo ""
echo "═══════════════════════════════════════════════════"
echo "          PULL REQUEST PREVIEW"
echo "═══════════════════════════════════════════════════"
echo ""
echo "TITLE: $PR_TITLE"
echo ""
echo "FROM: $CURRENT_BRANCH"
echo "TO: $BASE_BRANCH"
echo ""
echo "FILES CHANGED: $FILES_CHANGED files"
echo "COMMITS: $COMMITS_COUNT commits"
echo ""
echo "LABELS: $LABELS"
echo "REVIEWERS: $REVIEWERS"
echo ""
echo "DESCRIPTION:"
echo "$PR_DESCRIPTION"
echo ""
echo "═══════════════════════════════════════════════════"
```

## Step 5: Create PR Using GitHub CLI

```bash
BASE_BRANCH="$BASE_BRANCH"
IS_DRAFT="$IS_DRAFT"
PR_TITLE=$(jq -r '.title' pull-requests/pr-draft.json)
PR_DESCRIPTION=$(jq -r '.description' pull-requests/pr-draft.json)
LABELS=$(jq -r '.labels | join(",")' pull-requests/pr-draft.json)
REVIEWERS=$(jq -r '.suggested_reviewers | join(",")' pull-requests/pr-draft.json)

# Check GitHub CLI authenticated
if ! gh auth status &>/dev/null; then
  echo "❌ ERROR: GitHub CLI not authenticated"
  echo "Run: gh auth login"
  exit 1
fi

# Create PR
DRAFT_FLAG=""
if [ "$IS_DRAFT" = "true" ]; then
  DRAFT_FLAG="--draft"
fi

PR_URL=$(gh pr create \
  --title "$PR_TITLE" \
  --body "$PR_DESCRIPTION" \
  --base "$BASE_BRANCH" \
  $DRAFT_FLAG \
  --label "$LABELS" \
  --reviewer "$REVIEWERS" 2>&1)

if [ $? -ne 0 ]; then
  echo "❌ ERROR: Failed to create PR"
  echo "$PR_URL"
  exit 1
fi

# Extract PR number
PR_NUMBER=$(gh pr view --json number -q .number)

echo "✓ PR created successfully"
echo "  PR Number: #$PR_NUMBER"
echo "  URL: $PR_URL"
```

## Step 6: Post-PR Actions

```bash
PR_NUMBER="$PR_NUMBER"

# Trigger CI/CD if not automatic
if gh workflow list | grep -q "ci"; then
  echo "Triggering CI/CD workflow..."
  gh workflow run ci.yml --ref $(git branch --show-current) 2>/dev/null || true
fi

# Generate PR report
mkdir -p pull-requests
cat > pull-requests/pr-${PR_NUMBER}-report.json <<REPORT
{
  "pr_number": $PR_NUMBER,
  "pr_url": "$PR_URL",
  "pr_title": "$PR_TITLE",
  "pr_status": "${IS_DRAFT:-false}" == "true" ? "draft" : "open",
  "source_branch": "$CURRENT_BRANCH",
  "target_branch": "$BASE_BRANCH",
  "files_changed": $FILES_CHANGED,
  "commits_count": $COMMITS_COUNT,
  "reviewers_requested": $(jq '.suggested_reviewers' pull-requests/pr-draft.json),
  "labels_added": $(jq '.labels' pull-requests/pr-draft.json),
  "ci_triggered": true,
  "linked_issues": $(jq '.linked_issues' pull-requests/pr-draft.json),
  "description_generated": true,
  "created_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
}
REPORT

echo "✓ PR report saved"
```

## Step 7: Validate Output

```bash
PR_NUMBER="$PR_NUMBER"
PR_REPORT="pull-requests/pr-${PR_NUMBER}-report.json"

# Check PR report created
if [ ! -f "$PR_REPORT" ]; then
  echo "❌ ERROR: PR report not created"
  exit 1
fi

# Validate JSON
if ! jq empty "$PR_REPORT" 2>/dev/null; then
  echo "❌ ERROR: PR report is not valid JSON"
  exit 1
fi

# Check PR was created
if [ -z "$PR_NUMBER" ]; then
  echo "❌ ERROR: PR number not found"
  exit 1
fi

echo "✓ Output validation complete"
echo "  PR: #$PR_NUMBER"
echo "  Report: $PR_REPORT"
```

## Completion

```
═══════════════════════════════════════════════════
       PULL REQUEST CREATED SUCCESSFULLY ✓
═══════════════════════════════════════════════════

PR #$PR_NUMBER: $PR_TITLE
Command: /dev/create-pr
Version: 2.0.0

Pull Request Details:
  ✓ From: $CURRENT_BRANCH
  ✓ To: $BASE_BRANCH
  ✓ Status: ${IS_DRAFT == "true" ? "Draft" : "Open"}
  ✓ Files changed: $FILES_CHANGED
  ✓ Commits: $COMMITS_COUNT

Reviewers Requested: $REVIEWERS
Labels Added: $LABELS
CI/CD: ${CI_TRIGGERED ? "Triggered" : "Not triggered"}

URL: $PR_URL

Validations Passed:
  ✓ Prerequisites validated (not on main, branch pushed)
  ✓ PR created successfully
  ✓ AI description generated
  ✓ Output validation complete
  ✓ Quality threshold (≥0.90)

NEXT STEPS:

1. Monitor CI/CD checks:
   gh pr checks $PR_NUMBER --watch

2. Address review comments when received:
   - Respond to feedback
   - Make requested changes
   - Request re-review when ready

3. When approved and checks pass:
   /dev/merge $PR_NUMBER

4. View PR in browser:
   gh pr view $PR_NUMBER --web

═══════════════════════════════════════════════════

TIP: Use 'gh pr status' to check all your open PRs

═══════════════════════════════════════════════════
```

## Guidelines

- **PR Title**: Clear, concise, follows conventional commits format
- **PR Description**: Comprehensive, explains WHY not just WHAT
- **Before Creating**: Run /dev/review first, ensure all tests pass
- **Draft PRs**: Use --draft for work-in-progress PRs
- **Reviewers**: Request appropriate reviewers based on changes
- **CI/CD**: Ensure automated checks are triggered and monitored
- **Communication**: Respond promptly to review feedback
