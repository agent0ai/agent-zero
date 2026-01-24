---
description: Design the integration layer with state management, data fetching, and error handling
argument-hint: <spec-name>
allowed-tools: Task, Read, Write, Glob
---

# Design Integration

Spec: **$ARGUMENTS**

## Overview

This command designs the **integration layer** that connects frontend components to backend APIs. It creates patterns for data fetching, state management, caching, and error handling.

## Step 1: Check Prerequisites

```bash
if [ ! -d "agent-os/specs/$ARGUMENTS/contracts" ]; then
    echo "Error: No contracts found. Run /agent-os/design-contract $ARGUMENTS first."
    exit 1
fi
```

## Step 2: Launch Integration Architect Agent

Use the **integration-architect** agent:

```javascript
await Task({
  subagent_type: 'general-purpose',
  description: 'Design integration architecture',
  prompt: `
You are an integration architect. Design the integration layer for: ${ARGUMENTS}

1. ANALYZE CONTRACT & SPEC
   Read:
   - agent-os/specs/${ARGUMENTS}/contracts/api.ts
   - agent-os/specs/${ARGUMENTS}/contracts/types.ts
   - agent-os/specs/${ARGUMENTS}/spec.md

   Identify:
   - Data dependencies between components
   - Real-time requirements
   - User interaction patterns
   - Error scenarios

2. DESIGN QUERY ARCHITECTURE
   Create agent-os/specs/${ARGUMENTS}/integration/queries.ts:
   - Query client configuration
   - Query key factories
   - Cache invalidation patterns
   - Stale time configuration

3. DESIGN DATA FETCHING HOOKS
   Create agent-os/specs/${ARGUMENTS}/integration/hooks/:
   - One file per entity (useUsers.ts, etc.)
   - useQuery for fetching
   - useMutation for changes
   - Optimistic update patterns
   - Error handling

4. DESIGN API CLIENT
   Create agent-os/specs/${ARGUMENTS}/integration/api-client.ts:
   - Type-safe fetch wrapper
   - Error class extending contract errors
   - Consistent response handling
   - Authentication header handling

5. DESIGN ERROR HANDLING
   Create agent-os/specs/${ARGUMENTS}/integration/error-handling.tsx:
   - Error boundary components
   - Query error fallback
   - Error recovery patterns
   - Toast notification triggers

6. DESIGN LOADING STATES
   Create agent-os/specs/${ARGUMENTS}/integration/loading-states.tsx:
   - Skeleton components per view
   - Suspense wrappers
   - Empty state components
   - Spinner fallbacks

7. CREATE DOCUMENTATION
   Create agent-os/specs/${ARGUMENTS}/integration/README.md

Reference standards from .claude/standards/frontend/ for patterns.
  `
})
```

## Step 3: Review Integration Architecture

Verify the integration includes:

- [ ] React Query configuration
- [ ] Type-safe API client
- [ ] Hooks for all entities
- [ ] Optimistic update patterns
- [ ] Error boundaries
- [ ] Loading skeletons
- [ ] Empty states

## Completion

```
═══════════════════════════════════════════════════
        INTEGRATION ARCHITECTURE DESIGNED
═══════════════════════════════════════════════════

Spec: $ARGUMENTS

Integration Files:
  → integration/queries.ts (Query config)
  → integration/api-client.ts (API client)
  → integration/hooks/*.ts (Data hooks)
  → integration/error-handling.tsx (Error boundaries)
  → integration/loading-states.tsx (Loading UI)
  → integration/README.md (Documentation)

Patterns Implemented:
  ✓ Query caching
  ✓ Optimistic updates
  ✓ Cache invalidation
  ✓ Error recovery
  ✓ Loading states

NEXT STEPS:
→ Review integration patterns
→ Run /agent-os/implement-tasks $ARGUMENTS
→ Implementation will use these patterns

═══════════════════════════════════════════════════
```
