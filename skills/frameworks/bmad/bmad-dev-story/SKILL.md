---
name: "bmad-dev-story"
description: "Generate implementable developer stories from epics with technical specifications."
version: "1.0.0"
author: "Agent Zero Team"
tags: ["bmad", "development", "stories", "implementation"]
trigger_patterns:
  - "dev story"
  - "implement story"
  - "developer story"
  - "start development"
---

# BMAD: Developer Story

Take a user story from an epic and create a detailed, implementable developer specification.

## When to Use

- Starting work on a user story
- Need technical specification for implementation
- Handing off to developers

## Developer Story Format

```markdown
# Developer Story: [US-XXX] [Title]

## User Story
**As a** [persona]
**I want to** [capability]
**So that** [benefit]

## Technical Specification

### Overview
[Technical summary of what needs to be built]

### Implementation Steps
1. [ ] [Step 1 with file references]
2. [ ] [Step 2 with file references]
3. [ ] [Step 3 with file references]

### Files to Modify
| File | Changes |
|------|---------|
| `path/to/file.py` | [What to change] |

### Files to Create
| File | Purpose |
|------|---------|
| `path/to/new.py` | [What it does] |

### API Changes
```
[Endpoint specifications if applicable]
```

### Data Changes
```
[Schema changes if applicable]
```

### Dependencies
- [Package/library dependencies]
- [Service dependencies]

## Acceptance Tests

### Test 1: [Name]
```
Given: [Setup]
When: [Action]
Then: [Expected result]
```

### Test 2: [Name]
```
Given: [Setup]
When: [Action]
Then: [Expected result]
```

## Definition of Done
- [ ] Code complete
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Code reviewed
- [ ] Documentation updated
- [ ] Deployed to staging
```

## Process

1. **Load Epic Context**: Read epic and user story
2. **Analyze Requirements**: Understand what's needed
3. **Research Codebase**: Find relevant existing code
4. **Design Solution**: Plan implementation
5. **Write Specification**: Document steps
6. **Define Tests**: Acceptance criteria as tests
7. **Implement**: Follow the specification

## Output

After creating developer story:

```markdown
## Developer Story Ready: [US-XXX]

**Story**: [Title]
**Steps**: [X] implementation steps
**Tests**: [Y] acceptance tests

Ready to implement?
```

## Implementation Flow

Once story is ready:

1. Create feature branch
2. Follow implementation steps
3. Write tests as specified
4. Verify acceptance criteria
5. Create pull request
6. Complete Definition of Done

## Anti-Patterns

- Vague implementation steps
- Missing test specifications
- No file references
- Forgetting dependencies
- Skipping code review
