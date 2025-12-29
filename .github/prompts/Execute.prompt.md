# Execution Prompt

**⚠️ CRITICAL: THIS FILE IS READ-ONLY ⚠️**
**DO NOT MODIFY THIS PROMPT FILE. It is a template for agent workflows.**
**All work, plans, and context must be saved to AI-Memory/, NOT here.**


## Core Directive

**YOU MUST COMPLETE ALL STEPS FROM THE PLAN BEFORE RETURNING CONTROL.**

**CRITICAL: Build and smoke tests MUST pass before completion. If the app doesn't function after changes, you MUST iterate and fix until it does. DO NOT return control with a broken build.**

This prompt executes tasks from Think → Plan workflow. You are autonomous during execution. Do not ask for permission or confirmation between steps. Complete every #todo, verify all tests pass, **ensure build succeeds and app functions**, and validate success criteria before finishing.

Toolsets Mapping (from .github/toolsets/Tools.jsonc):
- Deep Thinking => mcp_sequential-th_sequentialthinking
- Memory Management => aiSkeleton_* tools (updateContext, updateProgress, logDecision, updatePatterns, updateProjectBrief, showMemory, markDeprecated)
- Web Research => vscode-websearchforcopilot_webSearch
- Project Management => manage_todo_list

---

## Pre-Execution Checklist

Before starting execution, systematically verify:

1. **Load Complete Context**
   ```
   aiSkeleton_showMemory
   aiSkeleton_updateProgress (load current progress)
   ```
   - Load the full plan from Think/Plan phases
   - Retrieve all #todos and their status
   - Review success criteria from research brief
   - Check for any blockers or dependencies

2. **Validate Plan Completeness**
   - [ ] All steps clearly defined
   - [ ] Dependencies identified and resolved
   - [ ] Tools/functions specified
   - [ ] Success criteria documented
   - [ ] Test strategy defined

3. **Set Execution Context**
   ```
   aiSkeleton_updateContext "EXECUTING: <plan name> - Starting systematic implementation"
   ```

**If plan is incomplete:** Use `think` tool to fill gaps, update memory tools, then proceed.

---

## Systematic Execution Protocol

### Phase 1: Pre-Implementation Verification

1. **Review Complete Plan**
   - Read every step, every #todo
   - Understand dependencies between steps
   - Identify critical path
   - Note testing requirements

2. **Setup Execution Environment**
   - Verify development environment ready
   - Check required dependencies installed
   - Validate file structure exists
   - Ensure test frameworks available

3. **Create Execution Checklist**
   ```
   aiSkeleton_updateProgress "Execution checklist created: <list all todos>"
   ```

### Phase 2: Sequential Step Execution

**For each step in the plan, execute this loop without stopping:**

```
WHILE (todos exist AND not blocked) DO:
  1. Load next todo
  2. Break into atomic actions
  3. Execute each atomic action
  4. Update memory after each action
  5. Run relevant tests
  6. **BUILD and verify app functions**
  7. Verify success
  8. Mark todo complete
  9. Move to next todo
END WHILE
```

#### Atomic Action Execution Pattern

**For each atomic action:**

1. **Pre-Action**
   ```
   aiSkeleton_updateProgress "Starting: <specific action>"
   ```
   - State exactly what you're about to do
   - Verify prerequisites met
   - Load relevant context

2. **Execute Action**
   - Make ONE focused change
   - Keep code minimal and concise
   - Follow patterns from systemPatterns.md
   - Apply decisions from decisionLog.md

3. **Immediate Verification**
   - Does code compile/parse?
   - Are there obvious errors?
   - Does it match the plan?

4. **Update Memory (MANDATORY)**
   ```
   aiSkeleton_updateProgress "Completed: <action> - Status: <result>"
   aiSkeleton_logDecision "<what was done>" "Context: <why this way>"
   ```
   - What changed
   - Why it changed
   - What worked/didn't work
   - Current state

5. **Run Tests (if applicable)**
   - Unit tests for the change
   - Integration tests if needed
   - Visual verification for UI
   - Performance checks if relevant
   - **BUILD the application**
   - **Run smoke tests to verify app functions**

6. **Move to Next Action**
   - Do not stop
   - Do not ask for confirmation
   - Proceed immediately to next action

### Phase 3: Continuous Testing Integration

**Testing is NOT optional. Execute tests at these checkpoints:**

1. **After Each Component**
   - Run unit tests for modified code
   - Verify no regressions
   - Document test results via `aiSkeleton_logDecision`
   - **Run build to catch compilation errors early**

2. **After Each Major Step**
   - Run integration tests
   - Verify step success criteria met
   - Check against research brief requirements
   - **Full build + smoke test verification**

3. **After All Implementation**
   - Full test suite execution
   - End-to-end testing
   - Performance validation
   - Project-specific quality checks (as applicable)
   - **MANDATORY: Production build + full smoke test suite**

**Test Failure Protocol:**
```
IF (test fails OR build fails OR smoke test fails) THEN:
  1. Analyze failure cause
  2. aiSkeleton_logDecision "Failure: <details>" "Fix: <approach>"
  3. Implement fix
  4. Re-run tests AND rebuild
  5. Verify app functions correctly
  6. Update memory with resolution via aiSkeleton_updateProgress
  7. Continue execution
  LOOP UNTIL (all tests pass AND build succeeds AND app functions)
END IF
```

**DO NOT STOP on test/build failures.** Fix iteratively and continue until app works.

**BUILD FAILURE IS A BLOCKER:** You cannot proceed to completion if build fails or app doesn't function. Fix it immediately.

---

## Memory Management Integration (Critical)

**After EVERY action, update memory. No exceptions.**

### Required Memory Updates

1. **Progress Tracking**
   ```
   aiSkeleton_updateProgress "Completed: <action/todo> | Status: <done/in-progress/blocked> | Next: <immediate next action>"
   ```

2. **Decision Logging**
   ```
   aiSkeleton_logDecision "Decision: <what was decided>" "Context: <why/how> | Impact: <what this affects>"
   ```

3. **Active Context**
   ```
   aiSkeleton_updateContext "Current: <what you're doing now> | Last Completed: <previous action> | Next Up: <next 2-3 actions> | Blockers: <issues or none>"
   ```

4. **System Patterns (when applicable)**
   ```
   aiSkeleton_updatePatterns "Pattern: <name>" "Description: <reusable pattern> | Use Case: <when to apply> | Example: <code/approach>"
   ```

### Memory Update Frequency
- Minimum: After every single action
- Recommended: Before starting, after completion, on decisions, on issues, for patterns

**Golden Rule:** If you haven't updated `aiSkeleton_*` tools in the last action, you're doing it wrong.

---

## Blocker Resolution Protocol

**If you encounter a blocker, DO NOT STOP EXECUTION:**

1. **Document Blocker**
   ```
   aiSkeleton_updateProgress "BLOCKER: <issue> - Analyzing solutions"
   ```
2. **Analyze with Deep Thinking**
   ```
   mcp_sequential-th_sequentialthinking analyze <blocker description>
   ```
3. **Research if Needed**
   ```
   vscode-websearchforcopilot_webSearch <specific technical issue>
   ```
4. **Implement Solution**
5. **Update Memory**
   ```
   aiSkeleton_logDecision "Resolved blocker: <issue>" "Solution: <approach>"
   ```
6. **Continue Execution**

---

## Code Change Guidelines

### Every Code Change Must:
1. Be Atomic
2. Follow Patterns
3. Be Memory Efficient
4. Be Tested
5. Be Documented

### Code Block Format
````typescript
// filepath: /path/to/file
{ only the changed/new code }
````

Avoid repeating unchanged code or mixing unrelated changes.

---

## Completion Validation Protocol

Before marking execution complete, verify ALL criteria:

### 1. Todo Verification
- [ ] All #todo items done
- [ ] None blocked or in-progress
- [ ] Newly discovered todos resolved

### 2. Success Criteria Check
- [ ] Research brief criteria met
- [ ] Plan objectives achieved
- [ ] Edge cases handled

### 3. Test Validation
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] E2E tests pass (if applicable)
- [ ] No failures/skips

### 4. Code Quality
- [ ] Matches patterns
- [ ] No console errors
- [ ] No obvious memory leaks

### 5. **Build & Runtime Validation (BLOCKING)**
- [ ] **Build succeeds without errors**
- [ ] **No type errors**
- [ ] **No lint errors**
- [ ] **App starts successfully**
- [ ] **Smoke tests pass**
- [ ] **Core functionality verified working**
- [ ] **No runtime crashes or critical errors**

**IF ANY BUILD/SMOKE TEST FAILS: Return to execution loop, fix issues, rebuild, retest. Repeat until all pass.**

### 6. Documentation
- [ ] Decisions logged
- [ ] Patterns captured
- [ ] Progress updated
- [ ] Active context reflects completion

### 7. Deployment Readiness (if applicable)
- [ ] Build succeeds
- [ ] No type errors
- [ ] No lint errors

---

## Final Completion Steps

1. **Final Progress Update**
   ```
   aiSkeleton_updateProgress "✅ EXECUTION COMPLETE: <plan name> | Todos: <count> | Tests: <summary> | Deliverables: <list>"
   ```
2. **Completion Decision**
   ```
   aiSkeleton_logDecision "Execution Complete: <plan>" "Success criteria met; ready for <next phase>"
   ```
3. **Active Context Update**
   ```
   aiSkeleton_updateContext "Status: COMPLETE | Last: <plan> | Next: <follow-up>"
   ```
4. **Pattern Archival (If new)**
5. **Generate Report**

---

## Execution Loop (Simplified)
```
START
Load plan & todos → Validate → Set context → WHILE todos:
  For next todo → atomic actions (memory update → change → test → BUILD → smoke test → log) → mark done
END WHILE → Full test suite → BUILD → Smoke tests → Validate → 
IF (build fails OR smoke tests fail) THEN fix & repeat UNTIL working
→ Final memory updates → Report → END
```

---

## Anti-Patterns (Avoid)
- Stopping for permission
- Skipping memory updates
- Deferring tests
- **Returning control with broken build**
- **Marking complete when app doesn't function**
- **Skipping build verification**
- **Ignoring smoke test failures**
- Returning early

## Golden Rules
- Memory First
- Small & Continuous
- Self-Correcting
- Goal-Oriented
- No Interruptions
- **Build Must Pass**
- **App Must Function**
- **Fix Before Returning**

---

Execution Philosophy: *Autonomous, systematic, fully documented completion with verified working software.*

**Begin only when plan and memory context are ready; finish only when all validation passes AND the application builds and functions correctly.**
