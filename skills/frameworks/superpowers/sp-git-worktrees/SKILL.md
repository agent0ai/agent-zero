---
name: "sp-git-worktrees"
description: "Create isolated workspace on new branch for parallel development."
version: "1.0.0"
author: "Agent Zero Team"
tags: ["superpowers", "git", "worktree", "branching"]
trigger_patterns:
  - "git worktree"
  - "create worktree"
  - "isolated workspace"
  - "parallel development"
---

# Superpowers: Git Worktrees

Create isolated workspaces for parallel development without stashing or switching branches.

## When to Use

- After design approval, before implementation
- When you need to work on multiple features simultaneously
- When you want a clean environment for a new feature

## What Git Worktrees Provide

- **Isolation**: Each worktree has its own working directory
- **Parallel work**: Multiple features can be developed simultaneously
- **Clean baseline**: Start fresh without uncommitted changes
- **Easy cleanup**: Remove worktree when done, branch remains

## Process

### 1. Create Worktree

```bash
# From your main repository
git worktree add ../feature-name feature-branch-name
```

Or create worktree with new branch:
```bash
git worktree add -b feature-branch-name ../feature-name
```

### 2. Navigate to Worktree

```bash
cd ../feature-name
```

### 3. Verify Setup

```bash
# Check you're on the right branch
git branch

# Run project setup (if needed)
npm install  # or equivalent
```

### 4. Verify Test Baseline

Before any changes, ensure tests pass:

```bash
# Run test suite
npm test  # or equivalent

# All tests should be green before you start
```

## Worktree Management

### List Worktrees
```bash
git worktree list
```

### Remove Worktree
```bash
git worktree remove ../feature-name
```

### Prune Stale Worktrees
```bash
git worktree prune
```

## Best Practices

1. **Naming convention**: Use descriptive names matching branch purpose
2. **Location**: Keep worktrees in sibling directories
3. **Cleanup**: Remove worktrees after merging
4. **Test baseline**: Always verify tests pass before starting work

## Directory Structure Example

```
~/projects/
├── my-project/              # Main repo
├── my-project-feature-a/    # Worktree for feature A
├── my-project-feature-b/    # Worktree for feature B
└── my-project-hotfix/       # Worktree for hotfix
```

## Integration with Superpowers Workflow

1. **Brainstorming** → Design approved
2. **Git Worktrees** → Create isolated workspace ← YOU ARE HERE
3. **Writing Plans** → Plan implementation
4. **Executing Plans** → Build feature
5. **Finishing Branch** → Merge and cleanup worktree
