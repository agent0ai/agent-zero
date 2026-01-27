---
name: "bmad-product-brief"
description: "Create a product brief defining vision, objectives, and high-level requirements."
version: "1.0.0"
author: "Agent Zero Team"
tags: ["bmad", "product", "planning", "vision"]
trigger_patterns:
  - "product brief"
  - "project vision"
  - "define product"
  - "start bmad"
---

# BMAD: Product Brief

Create a product brief that captures the vision, objectives, and business context for a new product or feature.

## When to Use

- Starting a new product or major feature
- Need to align stakeholders on vision
- Before creating detailed requirements

## Product Brief Structure

Create `docs/product-brief.md`:

```markdown
# Product Brief: [Product Name]

## Vision Statement
[One sentence describing the ultimate goal]

## Problem Statement
[What problem does this solve? Who has this problem?]

## Target Users
- **Primary**: [User type and characteristics]
- **Secondary**: [Other user types]

## Business Objectives
1. [Objective 1 - measurable]
2. [Objective 2 - measurable]
3. [Objective 3 - measurable]

## Success Metrics
| Metric | Target | Measurement |
|--------|--------|-------------|
| [Metric 1] | [Target] | [How measured] |
| [Metric 2] | [Target] | [How measured] |

## High-Level Requirements
1. [Core capability 1]
2. [Core capability 2]
3. [Core capability 3]

## Constraints
- **Technical**: [Any technical limitations]
- **Timeline**: [Target dates]
- **Budget**: [Resource constraints]
- **Compliance**: [Regulatory requirements]

## Out of Scope
- [What this is NOT]
- [Explicitly excluded features]

## Risks and Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| [Risk 1] | High/Med/Low | [Strategy] |

## Stakeholders
- **Owner**: [Who owns this]
- **Contributors**: [Who's involved]
- **Reviewers**: [Who approves]
```

## Gathering Information

Ask the user about:

1. **Problem Space**
   - What problem are you solving?
   - Who experiences this problem?
   - What's the impact of the problem?

2. **Solution Vision**
   - What does success look like?
   - How will users benefit?
   - What makes this different?

3. **Business Context**
   - What are the business goals?
   - What constraints exist?
   - Who are the stakeholders?

4. **Scope**
   - What must be included?
   - What should be excluded?
   - What's the timeline?

## Output

After creating the brief:

```markdown
## Product Brief Complete: [Product Name]

**Vision**: [One-liner]
**Objectives**: [X] defined
**Core Requirements**: [Y] identified

Brief saved to `docs/product-brief.md`

Ready to create detailed PRD? Use `bmad-create-prd`.
```

## Anti-Patterns

- Skipping problem definition
- Vague success metrics
- No stakeholder alignment
- Scope creep from day one
- Missing constraints
