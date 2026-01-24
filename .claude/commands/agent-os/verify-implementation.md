---
description: Verify complete end-to-end implementation and update roadmap
argument-hint: <spec-name>
allowed-tools: Task, Read, Write, Bash
---

# Verify Implementation

Spec: **$ARGUMENTS**

## Overview

This command:

1. Confirms all tasks are complete
2. Runs comprehensive test suite
3. Updates product roadmap
4. Generates final verification report

## Step 1: Check Prerequisites

```bash
# Count incomplete tasks
INCOMPLETE=$(grep -c "\[ \]" "agent-os/specs/$ARGUMENTS/tasks.md" 2>/dev/null || echo "0")
if [ "$INCOMPLETE" -gt 0 ]; then
    echo "Warning: $INCOMPLETE tasks still incomplete"
fi
```

## Step 2: Launch Implementation Verifier Agent

Use the **implementation-verifier** agent:

```javascript
await Task({
  subagent_type: 'general-purpose',
  description: 'Verify implementation',
  prompt: `
You are an implementation verifier. Verify: ${ARGUMENTS}

1. CHECK TASK COMPLETION
   - Read agent-os/specs/${ARGUMENTS}/tasks.md
   - Count [x] vs [ ] tasks
   - All tasks must be marked complete

   If incomplete tasks found:
   - List them
   - Recommend resuming implementation

2. UPDATE PRODUCT ROADMAP
   - Read agent-os/product/roadmap.md
   - Find the feature that was just implemented
   - Mark it complete: - [x] Feature name
   - Save updated roadmap

3. RUN TEST SUITE
   Execute all tests for this feature:
   - npm test -- --grep "${ARGUMENTS}"
   - or: pytest -k "${ARGUMENTS}"

   Verify:
   - All tests pass
   - No regressions in related tests

4. VISUAL VERIFICATION (if applicable)
   - Review screenshots in:
     agent-os/specs/${ARGUMENTS}/verification/screenshots/
   - Compare against visuals/
   - Confirm UI matches spec

5. GENERATE FINAL REPORT
   Create agent-os/specs/${ARGUMENTS}/verification/final-report.md with:
   - Status: VERIFIED / FAILED / PARTIAL
   - Task completion stats
   - Test results
   - Verification checklist
   - Screenshots captured
   - Issues found (if any)
   - Recommendations
  `
})
```

## Step 3: Review Results

Check final-report.md for:

- [ ] 100% task completion
- [ ] All tests passing
- [ ] Visual verification done (if applicable)
- [ ] Roadmap updated

## Completion

```
═══════════════════════════════════════════════════
        IMPLEMENTATION VERIFIED
═══════════════════════════════════════════════════

Spec: $ARGUMENTS
Status: [VERIFIED / FAILED]

Task Completion: [N]/[N] (100%)
Tests: [N] passing

Report: agent-os/specs/$ARGUMENTS/verification/final-report.md
Roadmap: Updated ✓

FEATURE READY FOR:
→ Code review
→ Deployment
→ User testing

═══════════════════════════════════════════════════
```
