---
name: "speckit-constitution"
description: "Define project constitution with principles, constraints, and non-negotiables."
version: "1.0.0"
author: "Agent Zero Team"
tags: ["speckit", "planning", "principles", "foundation"]
trigger_patterns:
  - "constitution"
  - "define principles"
  - "project rules"
---

# Spec Kit: Constitution

Define the foundational principles and constraints that guide all project decisions.

## When to Use

- Starting a new project with Spec Kit
- Need to establish non-negotiable rules
- Before creating specifications

## Constitution Structure

Create `CONSTITUTION.md`:

```markdown
# Project Constitution: [Project Name]

## Core Principles
1. [Principle 1 - e.g., "Security is non-negotiable"]
2. [Principle 2 - e.g., "Simple over clever"]
3. [Principle 3 - e.g., "Test everything"]

## Technology Stack
- Language: [Primary language]
- Framework: [Framework choice]
- Database: [Data storage]
- Infrastructure: [Hosting/deployment]

## Coding Standards
- Style Guide: [Reference]
- Formatting: [Tool, e.g., Prettier, Black]
- Linting: [Tool and config]

## Testing Requirements
- Unit Test Coverage: [Minimum %]
- Integration Tests: [Required/Optional]
- E2E Tests: [Required/Optional]

## Quality Gates
- [ ] All tests must pass
- [ ] No linting errors
- [ ] Code review required
- [ ] [Other gates]

## Non-Negotiables
- [Thing that cannot be compromised 1]
- [Thing that cannot be compromised 2]

## Conventions
- Naming: [Convention]
- File Structure: [Pattern]
- Commit Messages: [Format]
```

## Output

```markdown
## Constitution Created: [Project Name]

**Principles**: [X] defined
**Non-negotiables**: [Y] established

Constitution saved to `CONSTITUTION.md`

Ready to specify features? Use `speckit-specify`.
```
