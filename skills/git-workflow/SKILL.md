---
name: "git-workflow"
description: "Git workflow best practices for branching, committing, and collaboration. Use when working with version control."
version: "1.0.0"
author: "Agent Zero Team"
tags: ["git", "version-control", "branching", "collaboration", "workflow"]
trigger_patterns:
  - "git"
  - "commit"
  - "branch"
  - "merge"
  - "pull request"
---

# Git Workflow Skill

Best practices for version control and team collaboration.

## Branching Strategy

### Branch Naming Convention

```
<type>/<ticket-id>-<short-description>
```

**Types:**
- `feature/` - New features
- `bugfix/` - Bug fixes
- `hotfix/` - Urgent production fixes
- `refactor/` - Code refactoring
- `docs/` - Documentation updates
- `test/` - Adding tests
- `chore/` - Maintenance tasks

**Examples:**
```bash
feature/PROJ-123-add-user-authentication
bugfix/PROJ-456-fix-login-timeout
hotfix/PROJ-789-critical-security-patch
```

### Branch Workflow

```
main (production)
  │
  ├── develop (integration)
  │     │
  │     ├── feature/add-login
  │     ├── feature/add-dashboard
  │     └── bugfix/fix-signup
  │
  └── hotfix/security-patch (urgent fixes from main)
```

## Commit Messages

### Conventional Commits Format

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### Types

| Type | Description |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation |
| `style` | Formatting (no code change) |
| `refactor` | Code refactoring |
| `test` | Adding tests |
| `chore` | Maintenance |
| `perf` | Performance improvement |
| `ci` | CI/CD changes |

### Examples

```bash
# Feature
feat(auth): add JWT token refresh mechanism

# Bug fix with ticket reference
fix(api): resolve timeout issue on large payloads

Closes #123

# Breaking change
feat(api)!: change user endpoint response format

BREAKING CHANGE: User endpoint now returns nested
address object instead of flat fields.

# Multi-line with body
refactor(database): optimize user query performance

- Added composite index on (email, created_at)
- Removed N+1 query in user loader
- Cached frequently accessed user data

Performance improved from 500ms to 50ms for user list.
```

## Common Workflows

### Starting New Work

```bash
# 1. Update main branch
git checkout main
git pull origin main

# 2. Create feature branch
git checkout -b feature/PROJ-123-new-feature

# 3. Make changes and commit
git add .
git commit -m "feat(module): add new functionality"

# 4. Push and create PR
git push -u origin feature/PROJ-123-new-feature
```

### Syncing with Main

```bash
# Option 1: Rebase (preferred for feature branches)
git fetch origin
git rebase origin/main

# Option 2: Merge (when history preservation needed)
git fetch origin
git merge origin/main
```

### Interactive Rebase (Cleaning History)

```bash
# Squash last 3 commits
git rebase -i HEAD~3

# In editor, change 'pick' to 'squash' for commits to combine
pick abc1234 feat: add login form
squash def5678 fix: typo in form
squash ghi9012 style: format code
```

### Undoing Changes

```bash
# Undo last commit (keep changes)
git reset --soft HEAD~1

# Undo last commit (discard changes)
git reset --hard HEAD~1

# Undo specific file changes
git checkout -- path/to/file

# Revert a pushed commit (safe)
git revert <commit-hash>
```

### Stashing Work

```bash
# Save current changes
git stash save "WIP: feature description"

# List stashes
git stash list

# Apply most recent stash
git stash pop

# Apply specific stash
git stash apply stash@{2}

# Drop a stash
git stash drop stash@{0}
```

## Pull Request Guidelines

### Before Creating PR

1. **Rebase on latest main**
   ```bash
   git fetch origin
   git rebase origin/main
   ```

2. **Run tests locally**
   ```bash
   npm test  # or your test command
   ```

3. **Self-review your changes**
   ```bash
   git diff origin/main
   ```

4. **Clean up commits**
   - Squash fixup commits
   - Write clear commit messages

### PR Description Template

```markdown
## Summary
Brief description of changes

## Type of Change
- [ ] Feature
- [ ] Bug fix
- [ ] Refactor
- [ ] Documentation

## Changes Made
- Change 1
- Change 2
- Change 3

## Testing Done
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Screenshots (if applicable)
[Add screenshots here]

## Related Issues
Closes #123
```

### PR Best Practices

1. **Keep PRs Small**: < 400 lines ideally
2. **One Concern Per PR**: Don't mix features
3. **Descriptive Title**: Summarize the change
4. **Link Issues**: Reference related tickets
5. **Add Context**: Explain why, not just what
6. **Request Reviews**: Tag appropriate reviewers

## Resolving Conflicts

### Step-by-Step

```bash
# 1. Update your branch
git fetch origin

# 2. Rebase on main
git rebase origin/main

# 3. When conflicts occur, Git will pause
# Fix conflicts in your editor

# 4. After fixing each file
git add <fixed-file>

# 5. Continue rebase
git rebase --continue

# 6. If too complex, abort and try merge instead
git rebase --abort
git merge origin/main
```

### Conflict Markers

```
<<<<<<< HEAD
Your changes
=======
Their changes
>>>>>>> branch-name
```

## Git Hooks

### Pre-commit Hook Example

```bash
#!/bin/sh
# .git/hooks/pre-commit

# Run linter
npm run lint
if [ $? -ne 0 ]; then
    echo "Lint failed. Fix errors before committing."
    exit 1
fi

# Run tests
npm test
if [ $? -ne 0 ]; then
    echo "Tests failed. Fix tests before committing."
    exit 1
fi
```

### Commit Message Hook

```bash
#!/bin/sh
# .git/hooks/commit-msg

# Enforce conventional commits
commit_regex='^(feat|fix|docs|style|refactor|test|chore)(\(.+\))?: .{1,50}'

if ! grep -qE "$commit_regex" "$1"; then
    echo "Invalid commit message format."
    echo "Use: <type>(<scope>): <description>"
    exit 1
fi
```

## Useful Aliases

Add to `~/.gitconfig`:

```ini
[alias]
    # Status
    s = status -sb

    # Logging
    lg = log --oneline --graph --all
    last = log -1 HEAD --stat

    # Branching
    co = checkout
    cob = checkout -b
    br = branch -v

    # Committing
    cm = commit -m
    amend = commit --amend --no-edit

    # Stashing
    sl = stash list
    sp = stash pop

    # Diffing
    d = diff
    dc = diff --cached

    # Cleanup
    cleanup = "!git branch --merged | grep -v '\\*\\|main\\|develop' | xargs -n 1 git branch -d"
```
