---
description: Verify spec and tasks are complete and aligned with standards
argument-hint: <spec-name>
allowed-tools: Task, Read, Write
---

# Verify Spec

Spec: **$ARGUMENTS**

## Overview

This command:

1. Verifies all requirements are covered in spec
2. Confirms tasks cover all spec items
3. Checks alignment with project standards
4. Generates verification report

## Step 1: Check Prerequisites

```bash
if [ ! -f "agent-os/specs/$ARGUMENTS/tasks.md" ]; then
    echo "Error: No tasks.md found. Run /agent-os/create-tasks $ARGUMENTS first."
    exit 1
fi
```

## Step 2: Launch Spec Verifier Agent

Use the **spec-verifier** agent:

```javascript
await Task({
  subagent_type: 'general-purpose',
  description: 'Verify specification',
  prompt: `
You are a specifications verifier. Verify: ${ARGUMENTS}

1. LOAD ALL DOCUMENTS
   - Read agent-os/specs/${ARGUMENTS}/requirements.md
   - Read agent-os/specs/${ARGUMENTS}/spec.md
   - Read agent-os/specs/${ARGUMENTS}/tasks.md
   - Check agent-os/specs/${ARGUMENTS}/visuals/

2. VERIFY SPEC COMPLETENESS
   Check spec.md covers:
   - All user stories from requirements
   - All functional requirements
   - All non-functional requirements
   - All constraints acknowledged
   - Out-of-scope documented

3. VERIFY TASKS COVERAGE
   Check tasks.md covers:
   - Database tasks for data model
   - API tasks for backend requirements
   - Frontend tasks for UI requirements
   - Tests for acceptance criteria

4. CHECK STANDARDS ALIGNMENT
   Verify against .claude/standards/:
   - Tech stack matches
   - Coding conventions followed
   - Patterns consistent

5. GENERATE REPORT
   Create agent-os/specs/${ARGUMENTS}/verification-report.md with:
   - Verification status (PASS/FAIL/NEEDS REVIEW)
   - Requirements coverage table
   - Completeness checklist
   - Issues found
   - Recommendation
  `
})
```

## Step 3: Review Results

Check the verification report for:

- [ ] All requirements covered
- [ ] All tasks aligned
- [ ] No critical issues

## Completion

```
═══════════════════════════════════════════════════
        SPECIFICATION VERIFIED
═══════════════════════════════════════════════════

Spec: $ARGUMENTS
Status: [PASS/FAIL/NEEDS REVIEW]

Report: agent-os/specs/$ARGUMENTS/verification-report.md

NEXT STEPS:
→ If PASS: Run /agent-os/implement-tasks $ARGUMENTS
→ If FAIL: Address critical issues first

═══════════════════════════════════════════════════
```
