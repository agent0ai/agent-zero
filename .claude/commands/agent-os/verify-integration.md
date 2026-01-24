---
description: Verify end-to-end integration between frontend and backend
argument-hint: <spec-name>
allowed-tools: Task, Read, Write, Bash, Playwright
---

# Verify Integration

Spec: **$ARGUMENTS**

## Overview

This command performs **end-to-end integration verification** to ensure frontend and backend work together correctly, contracts are honored, and data flows properly.

## Step 1: Check Prerequisites

```bash
# Check implementation is complete
INCOMPLETE=$(grep -c "\[ \]" "agent-os/specs/$ARGUMENTS/tasks.md" 2>/dev/null || echo "0")
if [ "$INCOMPLETE" -gt 0 ]; then
    echo "Warning: $INCOMPLETE tasks still incomplete. Verification may be partial."
fi
```

## Step 2: Launch Full-Stack Verifier Agent

Use the **full-stack-verifier** agent:

```javascript
await Task({
  subagent_type: 'general-purpose',
  description: 'Verify full-stack integration',
  prompt: `
You are a full-stack integration verifier. Verify: ${ARGUMENTS}

1. LOAD CONTEXT
   Read:
   - agent-os/specs/${ARGUMENTS}/contracts/*.ts
   - agent-os/specs/${ARGUMENTS}/integration/*.ts
   - agent-os/specs/${ARGUMENTS}/spec.md
   - agent-os/specs/${ARGUMENTS}/tasks.md

   Also examine implementation:
   - Backend routes/controllers
   - Frontend components and hooks

2. VERIFY CONTRACT COMPLIANCE

   Backend:
   - Check all endpoints implemented
   - Verify request types match
   - Verify response types match
   - Check error codes implemented

   Frontend:
   - Check hooks use contract types
   - Verify API client matches contract
   - Check error handling covers all codes

3. GENERATE INTEGRATION TESTS
   Create agent-os/specs/${ARGUMENTS}/tests/integration.test.ts:

   Data Round-Trip Tests:
   - Create and verify display
   - Update and verify persistence
   - Delete and verify removal

   Error Propagation Tests:
   - Validation errors show messages
   - Not found handled
   - Network errors show retry

   Optimistic Update Tests:
   - Immediate UI updates
   - Rollback on error

   Cache Tests:
   - Invalidation after mutations
   - Refetch on window focus

4. RUN INTEGRATION VERIFICATION
   Execute:
   - npm run typecheck
   - npm test
   - npm run test:integration
   - npm run test:e2e (if available)

5. GENERATE VERIFICATION REPORT
   Create agent-os/specs/${ARGUMENTS}/verification/integration-report.md:
   - Contract compliance status
   - Data flow verification results
   - Integration test results
   - Issues found (critical, warnings, suggestions)
   - Recommendations

6. DETERMINE STATUS
   PASS: All critical checks pass
   PARTIAL: Some warnings but functional
   FAIL: Critical issues found
  `
})
```

## Step 3: Review Results

Check the verification report for:

- [ ] All contract endpoints compliant
- [ ] Data flow tests passing
- [ ] Error handling verified
- [ ] No critical issues

## Completion

```
═══════════════════════════════════════════════════
        FULL-STACK INTEGRATION VERIFIED
═══════════════════════════════════════════════════

Spec: $ARGUMENTS
Status: [PASS / FAIL / PARTIAL]

Contract Compliance:
  Backend: [N]/[N] endpoints
  Frontend: [N]/[N] hooks

Integration Tests:
  Passed: [N]
  Failed: [N]

Data Flow: [Verified / Issues Found]
Error Handling: [Verified / Issues Found]
Cache Behavior: [Verified / Issues Found]

Issues:
  Critical: [N]
  Warnings: [N]

Reports:
  → verification/integration-report.md
  → tests/integration.test.ts

NEXT STEPS:
→ Fix any critical issues
→ Review warnings
→ Feature ready for deployment when PASS

═══════════════════════════════════════════════════
```

## What Gets Verified

**Contract Compliance:**

- Every endpoint has correct types
- Every error code is handled
- Request/response shapes match

**Data Flow:**

- Create → appears in list
- Update → changes persist
- Delete → removes from list
- Pagination works

**Error Handling:**

- Validation → field errors shown
- Not found → appropriate message
- Unauthorized → redirect to login
- Network error → retry option

**State Management:**

- Optimistic updates work
- Rollback on error works
- Cache stays consistent
- No stale data displayed
