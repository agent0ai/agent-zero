---
description: Startup prompt for new chat sessions
---

# Startup Prompt

**⚠️ CRITICAL: THIS FILE IS READ-ONLY ⚠️**
**DO NOT MODIFY THIS PROMPT FILE. It is a template for agent workflows.**
**All work, plans, and context must be saved to AI-Memory/, NOT here.**


[New Task Or Continuing Session?]

## Instructions for Every New Chat

**Step 1: Determine Session Type**
- Ask whether this is a new task or continuation of a previous session.
- Check if AI-Memory exists and is populated.
- Check if MCPs are enabled; if not, enable them.

**Step 2: Route to Appropriate Workflow**
- If AI-Memory is empty or doesn't exist → Execute **Initial Setup** workflow
- If AI-Memory exists with content → Execute **Continuing Session** workflow
- If user explicitly requests new task → Execute **New Task** workflow

---

## Initial Setup Workflow (First Time in Workspace)

**This is a comprehensive onboarding process. Take your time and be thorough.**

### Phase 1: Workspace Discovery & Analysis

1. **Scan Repository Structure**
   ```bash
   # Get complete directory tree
   find . -type f -name "*.json" -o -name "*.md" -o -name "*.ts" -o -name "*.js" | head -100
   ls -la
   ```
   - Identify project type (extension, web app, library, CLI tool, etc.)
   - Map directory structure (common patterns: `src/`, `lib/`, `dist/`, `test/`, etc.)
   - Locate configuration files (package.json, tsconfig.json, etc.)
   - Find documentation (README.md, CONTRIBUTING.md, docs/)

2. **Read Core Documentation**
   - Read README.md thoroughly - understand purpose, features, usage
   - Read package.json - identify dependencies, scripts, metadata
   - Read CONTRIBUTING.md or similar if present
   - Check for existing architecture docs in docs/ or .github/

3. **Analyze Code Structure**
   - Identify entry points (main.ts, index.ts, extension.ts, etc.)
   - Map module organization and folder patterns
   - Identify key frameworks/libraries in use
   - Understand build/test/deploy tooling
   - Note any configuration patterns (env vars, settings, etc.)

4. **Technology Stack Inventory**
   - Programming language(s) and versions
   - Frameworks and major libraries
   - Build tools (webpack, vite, esbuild, tsc, rollup, etc.)
   - Testing frameworks (jest, vitest, mocha, pytest, etc.)
   - Development tools (ESLint, Prettier, formatters, linters, etc.)
   - Deployment/CI/CD (GitHub Actions, GitLab CI, Jenkins, etc.)

### Phase 2: Architecture & Pattern Analysis

1. **Identify Architectural Patterns**
   - Overall architecture style (MVC, plugin-based, microservices, etc.)
   - Code organization patterns (feature-based, layer-based, etc.)
   - Design patterns in use (factory, singleton, observer, etc.)
   - State management approach (if applicable)
   - Data flow patterns

2. **Document System Patterns**
   - File/folder naming conventions
   - Import/export patterns
   - Error handling approach
   - Logging and debugging patterns
   - Testing patterns and conventions
   - Configuration management patterns

3. **Identify Integration Points**
   - External APIs or services
   - Database or storage systems
   - Third-party libraries and their purposes
   - Platform-specific APIs (if applicable)
   - Runtime environment integrations

### Phase 3: Memory Bank Initialization

**First, create the memory bank (SQLite database + markdown files), then populate it:**

#### Step 1: Create Memory Bank (Required First)

If AI-Memory folder doesn't exist, create it via VS Code command:
```
Command Palette → "AI Skeleton: Create Memory Bank"
```
Or ask the user to run: `aiSkeleton.memory.create`

This initializes:
- `AI-Memory/memory.db` - SQLite database for fast queries
- `AI-Memory/*.md` files - Human-readable markdown (synced with database)

**Wait for confirmation before proceeding.**

#### Step 2: Populate Project Brief

Use `aiSkeleton_updateProjectBrief` to add project context to the database:
```
aiSkeleton_updateProjectBrief({
  "content": "## Project Overview\n[Comprehensive description from README and code analysis]\n\n## Purpose & Goals\n- [Primary purpose]\n- [Key objectives]\n- [Target users/audience]\n\n## Core Features\n- [Feature 1 with description]\n- [Feature 2 with description]\n\n## Technical Stack\n- **Language**: [Language + version]\n- **Framework**: [Framework + version]\n- **Key Libraries**: [List major dependencies]\n- **Build Tools**: [Build toolchain]\n- **Testing**: [Test framework]\n\n## Project Structure\n- [Key directories and their purposes]\n\n## Constraints & Requirements\n- [Technical constraints]\n- [Performance requirements]"
})
```

#### Step 3: Document System Patterns

Use `aiSkeleton_updatePatterns` for each major pattern discovered:
```
aiSkeleton_updatePatterns({
  "pattern": "Architecture Style",
  "description": "[High-level architecture description - MVC, plugin-based, etc.]"
})

aiSkeleton_updatePatterns({
  "pattern": "Code Organization",
  "description": "[Module organization approach - feature-based, layer-based, etc.]"
})

aiSkeleton_updatePatterns({
  "pattern": "Naming Conventions",
  "description": "[File/folder naming conventions, variable naming, etc.]"
})
```

#### Step 4: Set Initial Context

```
aiSkeleton_updateContext({
  "context": "Initial workspace setup complete. Project analyzed and documented. Ready for development work."
})
```

#### Step 5: Initialize Progress Tracking

```
aiSkeleton_updateProgress({
  "item": "Initial workspace analysis and memory bank setup",
  "status": "done"
})
```

#### Step 6: Log Setup Decision

```
aiSkeleton_logDecision({
  "decision": "Completed initial workspace analysis and memory setup",
  "rationale": "Analyzed [X] files, documented [Y] patterns, mapped [Z] dependencies. SQLite database initialized for fast memory queries."
})
```

### Phase 4: Validation & Summary

1. **Verify Memory Bank Active**
   ```
   aiSkeleton_showMemory
   ```
   Confirm:
   - [ ] Memory bank status shows ACTIVE
   - [ ] SQLite database initialized (memory.db exists)
   - [ ] Project brief contains comprehensive overview
   - [ ] System patterns documented
   - [ ] No critical gaps in understanding

2. **Generate Setup Summary**
   ```markdown
   ## Initial Setup Summary
   
   ### Project Identified
   - Type: [Extension/App/Library/etc.]
   - Name: [Project name]
   - Purpose: [Brief purpose]
   
   ### Analysis Completed
   - Files analyzed: [Count]
   - Directories mapped: [Count]
   - Patterns documented: [Count]
   - Dependencies cataloged: [Count]
   
   ### Memory Initialized
   - ✓ SQLite database created (memory.db)
   - ✓ Project brief populated
   - ✓ System patterns documented
   - ✓ Active context initialized
   - ✓ Progress tracking started
   - ✓ Decision log initialized
   
   ### Ready For
   - Feature development
   - Bug fixes
   - Refactoring
   - Testing
   - Documentation
   
   **Status**: Workspace fully analyzed. Ready for productive work.
   ```

3. **Print Completion Message**
   ```
   [MEMORY BANK: ACTIVE]
   
   Initial setup complete! I've analyzed the workspace and initialized memory bank.
   
   Ready for new instructions.
   ```

---

## New Task Checklist (Memory Exists, New Work)

1. **Load Current State from Database**
   ```
   aiSkeleton_showMemory
   ```
   The database query returns:
   - Project brief - understand project scope
   - System patterns - understand architecture  
   - Active context - check for ongoing work

2. **Clear Active Context**
   ```
   aiSkeleton_updateContext({ "context": "New task: [briefly describe if known]. Previous context cleared." })
   ```

3. **Archive Previous Work (if any)**
   - Mark completed items as done in progress
   - Clean up temporary files
   - Reset progress.md for new work

4. **Report Readiness**
   ```
   [MEMORY BANK: ACTIVE]
   
   Current project: [Project name from brief]
   Architecture: [Brief architecture summary from patterns]
   Previous work: [Summary of last completed work]
   
   Ready for new instructions.
   ```

---

## Continuing Session Checklist (Resume Previous Work)

1. **Load Complete Context from Database**
   ```
   aiSkeleton_showMemory
   ```
   The database returns all memory entries organized by type:
   - Project brief (goals, scope, tech stack)
   - Active context (current focus, blockers)
   - System patterns (architecture, conventions)
   - Decision log (recent technical decisions)
   - Progress (done/doing/next tasks)

2. **Analyze Current State**
   - Identify in-progress tasks from progress entries
   - Check for blockers in context entries
   - Review recent decisions from decision log
   - Understand current focus area

3. **Report Session Context**
   ```
   [MEMORY BANK: ACTIVE]
   
   Project: [Project name]
   Last session: [Summary of last work]
   
   Current tasks:
   - [In-progress task 1]
   - [In-progress task 2]
   
   Blockers: [List blockers or "None"]
   
   Ready to continue. What would you like to work on?
   ```

---

## Important Notes

**Initial Setup is Critical:**
- First-time setup should be thorough and comprehensive
- Take time to understand the codebase deeply
- Document everything you discover
- Ask clarifying questions if architecture is unclear
- This investment pays off in all future sessions

**Don't Rush:**
- Initial setup may take 5-10 minutes of analysis
- This is expected and valuable
- Thorough understanding prevents mistakes later
- Complete memory enables faster execution in future

**When in Doubt:**
- If unsure whether memory exists, check for AI-Memory/ directory
- If memory seems incomplete, re-run initial setup
- If memory seems stale, consider running Sync.prompt.md

---

**Tip:** You can always ask for a summary of the current context, memory, or workflow at any time.

This prompt ensures every session starts with proper context and orientation, enabling productive work from the first interaction.
