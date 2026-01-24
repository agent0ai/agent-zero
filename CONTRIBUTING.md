# Contributing to Quorum Earth Agent Zero Fork

## Overview

This fork is maintained by a single maintainer (@ckantrowitz) with agent-assisted code review.

## Branch Strategy

- `main` - Mirrors upstream `agent0ai/agent-zero` (auto-synced weekly)
- `quorum` - Stable customizations and development

**All customizations go to the `quorum` branch.**

## Adding New Customizations

### 1. Create a Feature Branch (Optional)

```bash
git checkout quorum
git checkout -b feature/my-new-feature
```

### 2. Make Your Changes

Follow existing patterns:
- New agents go in `agents/<AgentName>/`
- New prompts go in `prompts/`
- New extensions go in `python/extensions/`

### 3. Update CUSTOMIZATIONS.md

Add your customization to the inventory table with:
- Unique ID (C0XX)
- Name and type
- Purpose description
- File paths

### 4. Commit with Conventional Commits

```bash
git commit -m "feat(agents): add MyNewAgent for X purpose"
```

Format: `type(scope): description`

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`

### 5. Create Pull Request

```bash
git push origin feature/my-new-feature
# Then create PR to quorum branch on GitHub
```

### 6. Agent-Assisted Review

Comment on your PR:

```
@agent Please review this PR:
- Check code quality and consistency
- Verify no hardcoded secrets
- Ensure conventional commit format
- Confirm CUSTOMIZATIONS.md is updated
```

### 7. Merge

After agent approval, merge to `quorum`.

## Upstream Sync

The `main` branch syncs automatically. If you need to manually sync:

```bash
git checkout main
git fetch upstream
git merge upstream/main
git push origin main

git checkout quorum
git merge main
git push origin quorum
```

## Questions?

Open an issue or contact @ckantrowitz.
