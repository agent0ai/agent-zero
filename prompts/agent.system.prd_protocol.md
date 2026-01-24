# PRD (Product Requirements Document) Protocol

## Overview
This protocol defines how agents interact with PRDs across any project.
PRDs are versioned design records capturing architectural intent at specific points in time.

## Detecting PRDs in Projects
When working in a project, check for:
1. A file named `PRD_CONFIG.md` in the project root defining PRD location and conventions
2. Common PRD filenames: `*PRD*.md`, `*REQUIREMENTS*.md`, `*SPEC*.md`
3. Git tags with pattern `prd-v*` indicating versioned PRD history

## Before Architectural Changes
When modifying agent prompts, memory architecture, delegation paths, or system behavior:
1. Identify if the project has a PRD (check PRD_CONFIG.md or common patterns)
2. Read the relevant section of the PRD
3. Understand the current documented state
4. Identify what will change and whether it conflicts with documented architecture

## After Architectural Changes
When you have made changes that affect system architecture:
1. Update the relevant PRD section to reflect the new state
2. Update any Implementation Status tables if applicable
3. Add a changelog entry with format: `- YYYY-MM-DD: [Description]`
4. Commit with message: `docs(prd): [description of change]`
5. For significant changes (new components, major architecture shifts):
   - Create annotated tag: `git tag -a prd-vX.Y -m "[summary]"`
   - Push tag: `git push origin prd-vX.Y`

## What Counts as "Architectural Change"
- Adding/removing/renaming agents or components
- Changing delegation rules or communication patterns
- Modifying memory architecture or data flow
- Adding new verification protocols or quality gates
- Changing file structure conventions
- Altering security or access control patterns

## What Does NOT Require PRD Update
- Bug fixes that don't change architecture
- Content updates (data files, configuration values)
- Test additions that verify existing behavior
- Documentation typo fixes
- Performance optimizations that don't change interfaces

## PRD_CONFIG.md Format
Projects should create a `PRD_CONFIG.md` file specifying:
```markdown
# PRD Configuration

## Canonical PRD File
- Path: `[relative path to PRD file]`
- Example: `MULTI_AGENT_SYSTEM_PRD.md`

## Version Tag Pattern
- Pattern: `[git tag pattern]`
- Example: `prd-v*`

## Archive Location (optional)
- Path: `[relative path to archived versions]`
- Example: `archive/prd_versions/`

## Changelog Section
- Location: `[section name or path]`
- Example: `Section 19: Changelog` or `CHANGELOG.md`
```

## Version History Access
To view PRD version history:
- List versions: `git tag -l 'prd-v*'`
- View specific version: `git show prd-vX.Y:path/to/PRD.md`
- Compare versions: `git diff prd-vX.Y prd-vX.Z -- path/to/PRD.md`
