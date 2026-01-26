---
name: "bmad-create-architecture"
description: "Design technical architecture from PRD requirements."
version: "1.0.0"
author: "Agent Zero Team"
tags: ["bmad", "architecture", "design", "technical"]
trigger_patterns:
  - "create architecture"
  - "design system"
  - "architecture document"
---

# BMAD: Create Architecture

Design the technical architecture to fulfill PRD requirements.

## When to Use

- PRD is approved
- Need technical design before implementation
- Before breaking into epics

## Architecture Document Structure

Create `docs/architecture.md`:

```markdown
# Architecture Document: [Product Name]

## Overview
[High-level system description]

## Architecture Diagram
```
[Component diagram - ASCII or reference to image]
```

## Components

### Component 1: [Name]
- **Purpose**: [What it does]
- **Technology**: [Stack/framework]
- **Responsibilities**: [What it owns]
- **Interfaces**: [How it communicates]

## Data Model

### Entity: [Name]
| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| ... | ... | ... |

## API Design

### Endpoint: [Name]
- **Method**: GET/POST/etc
- **Path**: `/api/v1/...`
- **Request**: [Schema]
- **Response**: [Schema]

## Technology Decisions

### Decision 1: [What]
- **Options Considered**: [List]
- **Selected**: [Choice]
- **Rationale**: [Why]

## Security Architecture
- Authentication: [Approach]
- Authorization: [Approach]
- Data Protection: [Approach]

## Infrastructure
- Hosting: [Where]
- Scaling: [Strategy]
- Deployment: [Process]

## Performance Considerations
- [Caching strategy]
- [Database optimization]
- [CDN usage]

## Monitoring & Logging
- [What to monitor]
- [Logging approach]
- [Alerting strategy]
```

## Output

```markdown
## Architecture Complete: [Product Name]

**Components**: [X] main components
**APIs**: [Y] endpoints designed
**Entities**: [Z] data models

Architecture saved to `docs/architecture.md`

Ready to define epics? Use `bmad-create-epics`.
```
