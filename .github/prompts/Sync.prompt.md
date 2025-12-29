# Memory Sync Protocol

> **Purpose**: Scan the codebase and AI-Memory, synchronize knowledge, prune stale information, and ensure project state is accurately reflected.

---

## When to Use

- After major refactoring or architectural changes
- When starting a new session after extended absence
- Before major milestones or releases
- When you suspect memory drift from actual codebase
- Periodically (weekly recommended)

---

## Phase 1: Codebase Analysis

### Step 1.1 - Gather Current State

Scan the workspace to understand the actual current state:

```
1. List all top-level directories and key files
2. Identify main technologies, frameworks, dependencies
3. Find configuration files (package.json, tsconfig, etc.)
4. Locate entry points and core modules
5. Check recent git history (last 10-20 commits) for changes
```

### Step 1.2 - Extract Architecture

From the codebase, identify:

- **Core Components**: Main modules, services, classes
- **Data Flow**: How information moves through the system
- **External Integrations**: APIs, databases, third-party services
- **Build/Deploy Pipeline**: Scripts, CI/CD, tooling
- **Patterns in Use**: Design patterns, conventions, idioms

---

## Phase 2: Memory Analysis

### Step 2.1 - Read All Memory from Database

Query the memory database to get current state:

```
aiSkeleton_showMemory
```

This returns all memory entries organized by type:
- **projectBrief** - Product overview and goals
- **activeContext** - Current focus and blockers  
- **systemPatterns** - Architecture and patterns
- **decisionLog** - Historical decisions
- **progress** - Task tracking (done/doing/next)

### Step 2.2 - Identify Discrepancies

For each memory file, check:

| Check | Question |
|-------|----------|
| **Accuracy** | Does this still reflect reality? |
| **Completeness** | Is anything missing from current state? |
| **Relevance** | Is this still applicable or has it been superseded? |
| **Staleness** | Are there outdated entries that should be archived? |

---

## Phase 3: Synchronization

Use `aiSkeleton_*` tools to update the database. All updates are automatically persisted to both SQLite and markdown files.

### Step 3.1 - Update System Patterns

```
aiSkeleton_updatePatterns({
  "pattern": "[Pattern Name]",
  "description": "[Updated description]"
})
```

Apply these updates:
1. ADD new patterns discovered in codebase
2. Mark deprecated patterns using `aiSkeleton_markDeprecated`
3. UPDATE patterns that have evolved
4. VERIFY technical stack matches actual dependencies

### Step 3.2 - Update Project Brief

```
aiSkeleton_updateProjectBrief({
  "content": "[Updated project information]"
})
```

Apply these updates:
1. Refresh product description if scope changed
2. Update feature list (add new, mark completed)
3. Sync technical stack with actual dependencies
4. Update user/audience if it has evolved

### Step 3.3 - Update Active Context

```
aiSkeleton_updateContext({
  "context": "[Current focus and state]"
})
```

Apply these updates:
1. Clear stale context (entries older than 7-14 days)
2. Update current goals to match actual focus
3. Refresh blockers list
4. Add context for current work

### Step 3.4 - Update Progress

```
aiSkeleton_updateProgress({
  "item": "[Task description]",
  "status": "done" | "doing" | "next"
})
```

Apply these updates:
1. Move completed items to Done (verify against commits)
2. Update Doing to reflect actual current work
3. Refresh Next with upcoming priorities

### Step 3.5 - Update Decision Log

```
aiSkeleton_logDecision({
  "decision": "[Decision made]",
  "rationale": "[Why this was decided]"
})
```

Apply these updates:
1. Add any decisions made but not logged
2. Mark superseded decisions with `aiSkeleton_markDeprecated`
3. Keep all history (append-only) but annotate changes

---

## Phase 4: Validation

### Step 4.1 - Cross-Reference Check

Query the database to verify consistency:

```
aiSkeleton_showMemory
```

Check:
- [ ] Tech stack in project brief matches system patterns
- [ ] Current goals in context align with progress "doing" entries
- [ ] Recent decisions reflected in system patterns
- [ ] No contradictions between memory types

### Step 4.2 - Freshness Tags

All database entries are automatically timestamped. Verify entries have proper tags:

```
[TYPE:YYYY-MM-DD] Content here
```

Types: `CONTEXT`, `DECISION`, `PROGRESS`, `PATTERN`, `BRIEF`, `DEPRECATED`, `SUPERSEDED`

---

## Phase 5: Report

Generate a sync summary:

```markdown
## Memory Sync Complete - [DATE]

### Database Status
- Backend: [sql.js | better-sqlite3]
- Entries updated: [count]

### Changes Made:
- System Patterns: [X additions, Y updates, Z deprecations]
- Project Brief: [Summary of changes]
- Active Context: [Cleared N stale entries, added M new]
- Progress: [Moved X to Done, updated Doing]
- Decision Log: [Added N new decisions, marked M superseded]

### Discrepancies Found:
- [List any issues that need human attention]

### Recommendations:
- [Suggestions for follow-up actions]
```

---

## Cleanup Rules

### When to DEPRECATE (not delete):

- Pattern no longer used but historically relevant
- Decision was valid but circumstances changed
- Technology was replaced

### When to ARCHIVE:

- Context entries older than 30 days
- Completed progress items older than 60 days
- Keep in a `### Archived` section at file bottom

### Never Delete:

- Decision log entries (mark superseded instead)
- Pattern history (mark deprecated instead)
- Anything that explains "why" past choices were made

---

## Quick Sync Commands

For fast synchronization, use these memory tool commands:

```
AI Skeleton: Memory - Show Status     # Check current state
AI Skeleton: Memory - Show Memory     # View all memory
AI Skeleton: Memory - Update Context  # Quick context update
AI Skeleton: Memory - Update Progress # Quick progress update
AI Skeleton: Memory - Update Patterns # Quick pattern update
```

---

## Example Sync Session

```
User: "Run memory sync"

Agent Actions:
1. Read AI-Memory/*.md files
2. Scan workspace structure (ls, package.json, etc.)
3. Compare memory vs reality
4. Apply updates with proper tags
5. Report summary of changes
```

---

*This prompt ensures AI-Memory stays accurate, relevant, and useful across sessions.*
