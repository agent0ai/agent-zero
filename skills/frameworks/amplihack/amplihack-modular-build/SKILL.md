---
name: "amplihack-modular-build"
description: "Build code following the brick philosophy with self-contained modules."
version: "1.0.0"
author: "Agent Zero Team"
tags: ["amplihack", "modular", "build", "brick-philosophy"]
trigger_patterns:
  - "modular build"
  - "build module"
  - "brick pattern"
  - "self-contained"
---

# AMPLIHACK: Modular Build

Build code following the brick philosophy for self-contained, regeneratable modules.

## The Brick Philosophy

> "Each piece should be self-contained, testable, and replaceable without affecting others."

### Core Principles

1. **Self-Contained** - Module has everything it needs
2. **Single Responsibility** - One clear purpose
3. **Well-Defined Interface** - Clear inputs and outputs (studs)
4. **Regeneratable** - Can be rebuilt without breaking others
5. **Testable** - Can be tested in isolation

## Module Structure

```
module/
├── index.ts           # Public interface (studs)
├── implementation.ts  # Private implementation
├── types.ts          # Type definitions
├── constants.ts      # Module constants
└── module.test.ts    # Module tests
```

## Building a Module

### 1. Define the Interface (Studs)

Start with what the module exposes:

```typescript
// index.ts - The studs (public interface)
export interface ModuleInput {
  // What goes in
}

export interface ModuleOutput {
  // What comes out
}

export function moduleFunction(input: ModuleInput): ModuleOutput {
  // Implementation
}
```

### 2. Hide Implementation Details

Keep internals private:

```typescript
// implementation.ts - Private, can change freely
function internalHelper() {
  // Not exported, can be modified without affecting users
}
```

### 3. Define Clear Boundaries

Each module should have:

```markdown
## Module Specification

**Name:** {module-name}
**Purpose:** [Single sentence describing what it does]

**Inputs (Dependencies):**
- [Input 1]: [Type] - [Description]
- [Input 2]: [Type] - [Description]

**Outputs (Provides):**
- [Output 1]: [Type] - [Description]

**Invariants:**
- [Invariant 1] - [What must always be true]
```

### 4. Test in Isolation

```typescript
// module.test.ts
describe('ModuleName', () => {
  it('should [expected behavior]', () => {
    const input: ModuleInput = { ... };
    const result = moduleFunction(input);
    expect(result).toEqual({ ... });
  });
});
```

## Module Composition

Connect modules through their studs:

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Module A   │────▶│  Module B   │────▶│  Module C   │
│   (studs)   │     │   (studs)   │     │   (studs)   │
└─────────────┘     └─────────────┘     └─────────────┘
```

## Anti-Patterns to Avoid

| Anti-Pattern | Problem | Solution |
|-------------|---------|----------|
| **Reaching into internals** | Couples to implementation | Use only public interface |
| **Circular dependencies** | Can't reason about flow | Reorganize module boundaries |
| **God modules** | Too many responsibilities | Split into focused modules |
| **Leaky abstractions** | Implementation details escape | Better interface design |

## Build Checklist

Before considering a module complete:

- [ ] Single, clear purpose
- [ ] Well-defined interface (studs)
- [ ] No leaked implementation details
- [ ] Tests pass in isolation
- [ ] Can be regenerated independently
- [ ] Documentation for public interface

## Integration with AMPLIHACK

The modular build approach is used by:
- `amplihack-cascade` - Each stage produces a module
- `amplihack-auto` - Determines module boundaries
- Primary build agent - Creates regeneratable code
