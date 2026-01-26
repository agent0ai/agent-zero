---
name: "bmad-create-prd"
description: "Transform product brief into a detailed Product Requirements Document (PRD)."
version: "1.0.0"
author: "Agent Zero Team"
tags: ["bmad", "prd", "requirements", "documentation"]
trigger_patterns:
  - "create prd"
  - "product requirements"
  - "requirements document"
---

# BMAD: Create PRD

Transform the product brief into a comprehensive Product Requirements Document.

## When to Use

- Product brief is approved
- Need detailed requirements for development
- Before architecture design

## PRD Structure

Create `docs/prd.md`:

```markdown
# Product Requirements Document: [Product Name]

## Overview
[Summary from product brief]

## Background
[Context and why this is being built]

## Goals
[From product brief, refined]

## User Personas

### Persona 1: [Name]
- **Role**: [Job/function]
- **Goals**: [What they want to achieve]
- **Pain Points**: [Current frustrations]
- **Technical Proficiency**: [Level]

## User Stories

### Epic 1: [Title]

#### US-001: [Story Title]
**As a** [persona]
**I want to** [capability]
**So that** [benefit]

**Acceptance Criteria:**
- [ ] Given [context], when [action], then [result]
- [ ] Given [context], when [action], then [result]

**Priority**: High/Medium/Low
**Estimate**: S/M/L/XL

## Functional Requirements

### FR-001: [Requirement Title]
**Description**: [What the system must do]
**Rationale**: [Why this is needed]
**Acceptance**: [How to verify]

## Non-Functional Requirements

### Performance
- [Response time requirements]
- [Throughput requirements]

### Security
- [Authentication requirements]
- [Authorization requirements]
- [Data protection]

### Scalability
- [Expected load]
- [Growth projections]

### Reliability
- [Uptime requirements]
- [Recovery requirements]

## UI/UX Requirements
- [Key interface requirements]
- [Accessibility requirements]
- [Brand guidelines]

## Data Requirements
- [Data entities needed]
- [Storage requirements]
- [Retention policies]

## Integration Requirements
- [External systems]
- [APIs needed]
- [Data flows]

## Constraints
[From product brief, detailed]

## Assumptions
[What we're assuming is true]

## Dependencies
[What this depends on]

## Risks
[From product brief, detailed]

## Success Metrics
[From product brief, detailed measurement plans]

## Release Criteria
- [ ] All P0 requirements complete
- [ ] All tests pass
- [ ] Performance benchmarks met
- [ ] Security review complete
- [ ] Documentation complete
```

## Process

1. **Review Product Brief**: Ensure vision is clear
2. **Define Personas**: Flesh out user types
3. **Write User Stories**: Convert requirements to stories
4. **Detail Requirements**: Functional and non-functional
5. **Define Acceptance**: Clear criteria for each item
6. **Prioritize**: MoSCoW or similar prioritization

## Output

```markdown
## PRD Complete: [Product Name]

**User Stories**: [X] stories across [Y] epics
**Requirements**: [Z] functional, [W] non-functional
**Priority Distribution**: [breakdown]

PRD saved to `docs/prd.md`

Ready to design architecture? Use `bmad-create-architecture`.
```
