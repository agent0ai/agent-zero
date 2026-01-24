---
description: Create a feature branch and set up development environment
argument-hint: <feature-name> [issue-number]
allowed-tools: Bash, AskUserQuestion
model: claude-sonnet-4-5
timeout: 120
retry: 1
cost_estimate: 0.05-0.08

validation:
  input:
    feature_name:
      required: true
      min_length: 3
      pattern: "^[a-z0-9-]+$"
      error_message: "Feature name must be lowercase with hyphens (e.g., user-profile-upload)"
  output:
    schema: .claude/validation/schemas/dev/create-branch-output.json
    required_files:
      - '.git/refs/heads/feature/${feature_name}'
    quality_threshold: 0.90
    content_requirements:
      - "Branch created and pushed to remote"
      - "Upstream tracking set"
      - "Clean working directory"
      - "Up to date with base branch"

version: 2.0.0
changelog:
  - version: 2.0.0
    date: 2026-01-20
    changes:
      - "Migrated to modern pattern with comprehensive validation"
      - "Added input validation for feature name"
      - "Added output validation for branch creation"
      - "Streamlined from 289 lines to focused workflow"
      - "Enhanced safety checks for git operations"
  - version: 1.0.0
    date: 2025-08-20
    changes:
      - "Initial implementation with git workflow"
---

# Create Feature Branch

Feature: **$ARGUMENTS**

## Step 1: Validate Input & Parse Arguments

```bash
ARGS="$ARGUMENTS"
FEATURE_NAME=$(echo "$ARGS" | awk '{print $1}')
ISSUE_NUMBER=$(echo "$ARGS" | awk '{print $2}')

# Check feature name provided
if [ -z "$FEATURE_NAME" ]; then
  echo "❌ ERROR: Missing feature name"
  echo ""
  echo "Usage: /dev/create-branch <feature-name> [issue-number]"
  echo "Example: /dev/create-branch user-profile-upload"
  echo "Example: /dev/create-branch user-profile-upload 123"
  exit 1
fi

# Validate feature name format (lowercase with hyphens)
if ! echo "$FEATURE_NAME" | grep -qE '^[a-z0-9-]+$'; then
  echo "❌ ERROR: Invalid feature name format"
  echo "Feature name must be lowercase with hyphens"
  echo "Example: user-profile-upload"
  echo "Provided: $FEATURE_NAME"
  exit 1
fi

# Check minimum length
if [ ${#FEATURE_NAME} -lt 3 ]; then
  echo "❌ ERROR: Feature name too short (minimum 3 characters)"
  echo "Provided: $FEATURE_NAME"
  exit 1
fi

echo "✓ Input validated: $FEATURE_NAME"
[ -n "$ISSUE_NUMBER" ] && echo "  Issue: #$ISSUE_NUMBER"
```

## Step 2: Validate Git State

```bash
# Check if in git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
  echo "❌ ERROR: Not in a git repository"
  exit 1
fi

# Check for uncommitted changes
if ! git diff-index --quiet HEAD --; then
  echo "⚠️  WARNING: Uncommitted changes detected"
  git status --short
  echo ""
  read -p "Stash changes and continue? (yes/no): " CONFIRM
  if [ "$CONFIRM" = "yes" ]; then
    git stash push -m "Auto-stash before creating branch $FEATURE_NAME"
    echo "✓ Changes stashed"
  else
    echo "❌ Branch creation cancelled"
    exit 1
  fi
fi

# Get current branch
CURRENT_BRANCH=$(git branch --show-current)
echo "Current branch: $CURRENT_BRANCH"

# Determine base branch (main, master, or develop)
if git show-ref --verify --quiet refs/heads/main; then
  BASE_BRANCH="main"
elif git show-ref --verify --quiet refs/heads/master; then
  BASE_BRANCH="master"
elif git show-ref --verify --quiet refs/heads/develop; then
  BASE_BRANCH="develop"
else
  echo "❌ ERROR: Could not find base branch (main, master, or develop)"
  exit 1
fi

echo "Base branch: $BASE_BRANCH"

# Check if on base branch, if not, offer to switch
if [ "$CURRENT_BRANCH" != "$BASE_BRANCH" ]; then
  echo "⚠️  WARNING: Not on $BASE_BRANCH branch"
  read -p "Switch to $BASE_BRANCH and continue? (yes/no): " CONFIRM
  if [ "$CONFIRM" = "yes" ]; then
    git checkout $BASE_BRANCH
    echo "✓ Switched to $BASE_BRANCH"
  else
    echo "Creating branch from $CURRENT_BRANCH (not recommended)"
  fi
fi

echo "✓ Git state validated"
```

## Step 3: Sync with Remote

```bash
BASE_BRANCH="$BASE_BRANCH"

# Fetch latest from remote
echo "Fetching latest changes from remote..."
git fetch origin

# Pull latest changes
echo "Pulling latest $BASE_BRANCH..."
git pull origin $BASE_BRANCH

if [ $? -ne 0 ]; then
  echo "❌ ERROR: Failed to pull latest changes"
  echo "Resolve conflicts and try again"
  exit 1
fi

echo "✓ Synced with remote"
```

## Step 4: Create Branch

```bash
FEATURE_NAME="$FEATURE_NAME"
ISSUE_NUMBER="$ISSUE_NUMBER"

# Construct branch name
if [ -n "$ISSUE_NUMBER" ]; then
  BRANCH_NAME="feature/${ISSUE_NUMBER}-${FEATURE_NAME}"
else
  BRANCH_NAME="feature/${FEATURE_NAME}"
fi

echo "Creating branch: $BRANCH_NAME"

# Check if branch already exists
if git show-ref --verify --quiet refs/heads/$BRANCH_NAME; then
  echo "❌ ERROR: Branch already exists locally: $BRANCH_NAME"
  read -p "Checkout existing branch? (yes/no): " CONFIRM
  if [ "$CONFIRM" = "yes" ]; then
    git checkout $BRANCH_NAME
    echo "✓ Checked out existing branch"
    exit 0
  else
    echo "Branch creation cancelled"
    exit 1
  fi
fi

# Check if branch exists on remote
if git ls-remote --exit-code --heads origin $BRANCH_NAME >/dev/null 2>&1; then
  echo "❌ ERROR: Branch already exists on remote: $BRANCH_NAME"
  read -p "Checkout remote branch? (yes/no): " CONFIRM
  if [ "$CONFIRM" = "yes" ]; then
    git checkout -b $BRANCH_NAME origin/$BRANCH_NAME
    echo "✓ Checked out remote branch"
    exit 0
  else
    echo "Branch creation cancelled"
    exit 1
  fi
fi

# Create and checkout new branch
git checkout -b $BRANCH_NAME

if [ $? -ne 0 ]; then
  echo "❌ ERROR: Failed to create branch"
  exit 1
fi

echo "✓ Branch created: $BRANCH_NAME"
```

## Step 5: Push to Remote

```bash
BRANCH_NAME="$BRANCH_NAME"

# Push branch to remote with upstream tracking
echo "Pushing branch to remote..."
git push -u origin $BRANCH_NAME

if [ $? -ne 0 ]; then
  echo "❌ ERROR: Failed to push branch to remote"
  exit 1
fi

echo "✓ Branch pushed to remote with upstream tracking"
```

## Step 6: Link to GitHub Issue (Optional)

```bash
BRANCH_NAME="$BRANCH_NAME"
ISSUE_NUMBER="$ISSUE_NUMBER"

if [ -n "$ISSUE_NUMBER" ] && command -v gh &> /dev/null; then
  echo "Linking branch to issue #$ISSUE_NUMBER..."

  # Add comment to issue
  gh issue comment $ISSUE_NUMBER --body "🚀 Started development in branch \`$BRANCH_NAME\`" 2>/dev/null

  if [ $? -eq 0 ]; then
    echo "✓ Linked to issue #$ISSUE_NUMBER"
  else
    echo "⚠️  Could not link to issue (gh cli may not be authenticated)"
  fi
fi
```

## Step 7: Optional Environment Setup

```bash
# Ask if user wants to set up development environment
read -p "Set up development environment? (install deps, run migrations) (yes/no): " SETUP_ENV

if [ "$SETUP_ENV" = "yes" ]; then
  echo "Setting up development environment..."

  # Install dependencies (if package.json exists)
  if [ -f "package.json" ]; then
    echo "Installing npm dependencies..."
    npm install
  fi

  # Run migrations (if migration script exists)
  if [ -f "package.json" ] && npm run | grep -q "migrate"; then
    read -p "Run database migrations? (yes/no): " RUN_MIGRATIONS
    if [ "$RUN_MIGRATIONS" = "yes" ]; then
      npm run migrate
    fi
  fi

  echo "✓ Environment setup complete"
fi
```

## Step 8: Validate Output

```bash
BRANCH_NAME="$BRANCH_NAME"
FEATURE_NAME="$FEATURE_NAME"

# Verify branch was created
if ! git show-ref --verify --quiet refs/heads/$BRANCH_NAME; then
  echo "❌ ERROR: Branch not found locally"
  exit 1
fi

# Verify branch has upstream
UPSTREAM=$(git rev-parse --abbrev-ref --symbolic-full-name @{u} 2>/dev/null)
if [ -z "$UPSTREAM" ]; then
  echo "❌ ERROR: Upstream tracking not set"
  exit 1
fi

# Verify clean working directory
if ! git diff-index --quiet HEAD --; then
  echo "⚠️  WARNING: Working directory not clean"
fi

echo "✓ Output validation complete"
echo "  Branch: $BRANCH_NAME"
echo "  Upstream: $UPSTREAM"
```

## Completion

```
═══════════════════════════════════════════════════
     FEATURE BRANCH CREATED SUCCESSFULLY ✓
═══════════════════════════════════════════════════

Feature: $FEATURE_NAME
Branch: feature/[branch-name]
Command: /dev/create-branch
Version: 2.0.0

Branch Status:
  ✓ Created locally
  ✓ Pushed to remote
  ✓ Upstream tracking set
  ✓ Based on: [base-branch]
  ${ISSUE_NUMBER ? '✓ Linked to issue #' + ISSUE_NUMBER : ''}

Development Environment:
  ${SETUP_ENV === 'yes' ? '✓ Dependencies installed' : '○ Not configured'}
  ${RUN_MIGRATIONS === 'yes' ? '✓ Migrations run' : '○ Not run'}

Validations Passed:
  ✓ Input validation (feature name valid)
  ✓ Output validation (branch created)
  ✓ Git state validated
  ✓ Synced with remote
  ✓ Quality threshold (≥0.90)

NEXT STEPS:

1. Start implementing the feature:
   /dev/implement $FEATURE_NAME

2. Or manually start coding:
   - Make changes
   - Commit frequently (git commit -m "...")
   - Push regularly (git push)

3. Run tests as you develop:
   /dev/test

4. When ready for review:
   /dev/create-pr

HAPPY CODING! 🚀

═══════════════════════════════════════════════════
```

## Guidelines

- **Branch Naming**: Use lowercase with hyphens (feature/user-profile-upload)
- **Include Issue Number**: Link to GitHub issues when applicable
- **Sync First**: Always pull latest before creating branch
- **Clean State**: Stash or commit changes before creating branch
- **Push Immediately**: Push to remote as backup
- **Small Branches**: Keep feature branches focused and short-lived
- **Regular Commits**: Commit frequently with clear messages
