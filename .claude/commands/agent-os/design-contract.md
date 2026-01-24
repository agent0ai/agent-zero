---
description: Create unified API contracts shared between frontend and backend
argument-hint: <spec-name>
allowed-tools: Task, Read, Write, Glob, Grep
---

# Design Contract

Spec: **$ARGUMENTS**

## Overview

This command creates the **unified API contract** that both frontend and backend will implement against. The contract is the source of truth - design it BEFORE implementation.

## Why Contract-First?

- **Type safety across the stack** - Same types in frontend and backend
- **Early error detection** - Type errors caught at compile time
- **Clear API surface** - Frontend knows exactly what to expect
- **Parallel development** - Teams can work independently against contract

## Step 1: Check Prerequisites

```bash
if [ ! -f "agent-os/specs/$ARGUMENTS/spec.md" ]; then
    echo "Error: No spec.md found. Run /agent-os/write-spec $ARGUMENTS first."
    exit 1
fi
```

## Step 2: Launch Contract Designer Agent

Use the **contract-designer** agent:

```javascript
await Task({
  subagent_type: 'general-purpose',
  description: 'Design API contract',
  prompt: `
You are an API contract designer. Create unified contracts for: ${ARGUMENTS}

1. ANALYZE SPECIFICATION
   Read:
   - agent-os/specs/${ARGUMENTS}/spec.md
   - agent-os/specs/${ARGUMENTS}/requirements.md
   - agent-os/specs/${ARGUMENTS}/visuals/

   Extract:
   - Data entities and fields
   - User actions requiring API calls
   - Data display requirements
   - Error scenarios

2. IDENTIFY API SURFACE
   Map UI requirements to endpoints:
   - What data needs to be fetched?
   - What mutations does the user perform?
   - What real-time updates are needed?

3. CREATE CONTRACT FILES
   Create agent-os/specs/${ARGUMENTS}/contracts/:

   types.ts - Entity and request/response types
   - All shared data structures
   - Request body types
   - Response types
   - Pagination types

   errors.ts - Error codes and format
   - Standardized error codes
   - Error response shape
   - HTTP status mapping

   api.ts - Complete API contract
   - Endpoint definitions
   - Request/response per endpoint
   - Possible errors per endpoint
   - Type helpers for type-safe calls

   hooks-template.ts - Frontend hook templates
   - useQuery patterns
   - useMutation patterns
   - Optimistic update patterns

   routes-template.ts - Backend route templates
   - Route handler patterns
   - Validation patterns
   - Error handling patterns

   README.md - Contract documentation

4. VALIDATE COMPLETENESS
   Ensure:
   - Every UI data need has an endpoint
   - Every user action has a mutation
   - All error cases are defined
   - Types are complete (no 'any')

Reference standards from .claude/standards/ for alignment.
  `
})
```

## Step 3: Review Contract

Verify the contract includes:

- [ ] All entities from spec
- [ ] All endpoints for data fetching
- [ ] All endpoints for mutations
- [ ] Complete error code coverage
- [ ] Type-safe helper types

## Step 4: Integration Point

After contract is created, the workflow continues:

```
design-contract → create-tasks → implement-tasks
                      ↓
         Tasks now reference contract types
         Both frontend and backend import from contract
```

## Completion

```
═══════════════════════════════════════════════════
        API CONTRACT DESIGNED
═══════════════════════════════════════════════════

Spec: $ARGUMENTS

Contract Files:
  → contracts/types.ts (Shared types)
  → contracts/errors.ts (Error codes)
  → contracts/api.ts (API contract)
  → contracts/hooks-template.ts (Frontend patterns)
  → contracts/routes-template.ts (Backend patterns)
  → contracts/README.md (Documentation)

NEXT STEPS:
→ Review the contract with team
→ Run /agent-os/create-tasks $ARGUMENTS
→ Tasks will reference contract for type-safe implementation

═══════════════════════════════════════════════════
```

## Contract Benefits

**For Frontend:**

- Know exactly what API returns
- Type-safe API client
- Autocomplete for responses
- Compile-time error detection

**For Backend:**

- Clear implementation target
- Request validation schemas
- Response type enforcement
- Error code standardization

**For Both:**

- Single source of truth
- Contract changes require both sides to update
- No more "API changed without telling frontend"
