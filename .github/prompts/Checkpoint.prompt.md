---
description: Comprehensive memory bank checkpoint and update workflow
version: "1.0.0"
---

# AI-Memory Checkpoint

**⚠️ CRITICAL: THIS FILE IS READ-ONLY ⚠️**
**DO NOT MODIFY THIS PROMPT FILE. It is a template for agent workflows.**
**All work, plans, and context must be saved to AI-Memory/, NOT here.**


This prompt guides a comprehensive review and update of all memory bank files, captures recent progress, documents decisions, and generates a commit message summarizing the session.

## Instructions

Run this checkpoint at the end of a coding session or when significant work has been completed.

### Step 1: Review Current State

1. **Query memory database**:
   ```
   aiSkeleton_showMemory
   ```
   This returns all memory entries organized by type:
   - Project brief - Understand the project scope
   - Active context - Current goals and blockers
   - System patterns - Architectural patterns
   - Decision log - Past decisions
   - Progress - Recent work (done/doing/next)

2. **Gather session context**:
   - Review recent git changes: `git status` and `git diff`
   - Check for new or modified files in key directories:
     - Source directories (`src/`, `lib/`, etc.)
     - Configuration files (`.github/`, `.vscode/`, root configs)
   - Note any test runs, builds, or deployments attempted

### Step 2: Update Memory Database

Update the database using `aiSkeleton_*` tools. All updates persist to both SQLite and markdown files automatically.

#### Active Context
Update current goals and blockers:
```
aiSkeleton_updateContext({
  "context": "[Current focus, blockers, and recent changes]"
})
```
- Remove completed goals
- Add new goals discovered during this session

#### Progress
Track task completion:
```
aiSkeleton_updateProgress({
  "item": "[Task description]",
  "status": "done" | "doing" | "next"
})
```
- Move completed items to "done"
- Update "doing" with current in-progress work
- Update "next" with planned upcoming tasks

#### Decision Log
Document decisions made:
```
aiSkeleton_logDecision({
  "decision": "[What was decided]",
  "rationale": "[Why this decision was made]"
})
```

#### System Patterns
Document new or updated patterns:
```
aiSkeleton_updatePatterns({
  "pattern": "[Pattern name]",
  "description": "[Pattern description and usage]"
})
```
Categories:
- **Architectural Patterns**: High-level system design
- **Design Patterns**: Code organization and structure
- **Common Idioms**: Project-specific conventions

#### Project Brief
Update ONLY if project goals/scope changed:
```
aiSkeleton_updateProjectBrief({
  "content": "[Updated project goals/scope/constraints]"
})
```
**IMPORTANT:** Use for project-level info ONLY:
- Top-level goals and objectives
- Project scope and boundaries
- Technical constraints
- Target users/audience

**DO NOT use for:**
- Research findings (use `aiSkeleton_saveResearch`)
- Implementation plans (use `aiSkeleton_savePlan`)
- Task details (use `aiSkeleton_updateProgress`)

### Step 3: Review Workflow and Instruction Files

Check if any workflow or instruction files need updates:

1. **Review `.github/workflows/`** for CI/CD changes
2. **Review `.vscode/settings.json`** and `mcp.json` for tooling updates
3. **Review root configuration files**:
   - `package.json` - dependency changes
   - Build configuration files - framework-specific settings
   - `tsconfig.json` / language config - compiler/interpreter settings
   - Test configuration files - testing framework settings

4. **Document recommendations**:
   - Workflow improvements discovered
   - Configuration optimizations
   - Tooling enhancements
   - Process refinements

### Step 4: Generate Summary Report

Create a structured summary:

```markdown
## Checkpoint Summary

### Session Overview
[Brief description of work completed]

### Files Modified
- [List key files changed]

### Decisions Made
- [List major decisions from this session]

### Progress Updates
**Completed:**
- [Items moved to Done]

**In Progress:**
- [Current work]

**Blocked:**
- [Any blockers identified]

### Recommendations
- [Workflow improvements]
- [Configuration updates]
- [Process changes]

### Next Steps
- [Immediate next actions]
- [Future work to consider]
```

### Step 5: Generate Commit Message

Based on the session summary, generate a conventional commit message:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:** feat, fix, docs, style, refactor, test, chore, build, ci, perf

**Guidelines:**
- Subject: Imperative mood, max 72 characters
- Body: Explain what and why (not how)
- Footer: Breaking changes, issue references

**Example:**
```
chore(memory): update memory bank checkpoint workflow

- Added comprehensive checkpoint prompt for session reviews
- Updated progress tracking with recent test coverage work
- Documented build configuration decision
- Enhanced system patterns with fallback strategy details

Related to ongoing feature development and deployment workflow improvements.
```

### Step 6: Validation

Before completing:

- [ ] All memory files have current dates
- [ ] DecisionLog entries follow table format
- [ ] Progress items are timestamped
- [ ] Active blockers are clearly documented
- [ ] System patterns reflect current architecture
- [ ] Commit message follows conventional commits format
- [ ] Recommendations are actionable and specific

### Step 7: Cleanup & Archive

Organize completed work and remove temporary files:

1. **Identify Temporary Files**
   - Search workspace for temp files created during Think/Plan/Execute phases:
     - Research briefs (temporary markdown files)
     - Draft plans (if saved locally)
     - Working notes (if any)
     - Build artifacts or cache files
   - Do NOT delete files in `.github/`, source code, or config files

2. **Create Archive Structure**
   ```bash
   AI-Memory/archive/YYYY-MM-DD-<tag>/
   ├── research/          # Completed research documents
   ├── plans/             # Completed execution plans
   ├── notes/             # Working notes from session
   └── summary.md         # Session checkpoint summary
   ```

3. **Move Completed Research & Plans**
   - Move any research brief files to `AI-Memory/archive/<date-tag>/research/`
   - Move any execution plan documents to `AI-Memory/archive/<date-tag>/plans/`
   - Move working notes to `AI-Memory/archive/<date-tag>/notes/`
   - Preserve original structure and naming for audit trail

4. **Remove Temporary Files**
   - Delete temporary markdown files from workspace root
   - Clean up draft files not in version control
   - Remove build artifacts or cache directories
   - Verify with `git status` that only actual source changes remain

5. **Update Active Memory**
   ```
   aiSkeleton_updateContext "Cleanup complete: Session archived to AI-Memory/archive/<date-tag>; Workspace cleaned"
   ```

6. **Verification Checklist**
   - [ ] Archive directory created with proper date-tag structure
   - [ ] All completed research/plans moved to archive
   - [ ] Temporary files removed from workspace
   - [ ] `git status` shows only intentional changes
   - [ ] No untracked files except .gitignore'd items
   - [ ] Memory bank updated with archive location

## Usage

To run this checkpoint:

1. Say "Checkpoint" or "Run checkpoint" to the assistant
2. The assistant will execute all steps above using `aiSkeleton_*` tools
3. Review the generated summary and commit message
4. Manually commit using the provided message, or edit as needed

## Output Format

The assistant should respond with:

1. **Status**: `[MEMORY BANK: UPDATING]` at start
2. **Updates**: Confirmation of each file updated via `aiSkeleton_*` tools
3. **Summary**: Structured session summary
4. **Commit Message**: Ready-to-use git commit message
5. **Final Status**: `[MEMORY BANK: ACTIVE]`

---

This checkpoint ensures consistent project memory maintenance and provides clear session documentation for future reference.
