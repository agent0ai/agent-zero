---
name: "amplihack-debate"
description: "Multi-perspective debate workflow for complex decisions."
version: "1.0.0"
author: "Agent Zero Team"
tags: ["amplihack", "debate", "decision-making"]
trigger_patterns:
  - "debate"
  - "multiple perspectives"
  - "decision"
---

# AMPLIHACK: Debate

Facilitate multi-perspective debate for complex technical decisions.

## When to Use

- Multiple valid approaches exist
- High-stakes technical decisions
- Need to surface trade-offs
- Want rigorous analysis

## Debate Structure

### Participants (Perspectives)
- **Advocate**: Argues for proposed approach
- **Critic**: Challenges assumptions, finds weaknesses
- **Pragmatist**: Focuses on practical concerns
- **Moderator**: Synthesizes and drives to conclusion

### Debate Rounds

#### Round 1: Initial Arguments
Each perspective presents their view:
```markdown
### Advocate
[Arguments for approach]

### Critic
[Challenges and concerns]

### Pragmatist
[Practical considerations]
```

#### Round 2: Rebuttals
Perspectives respond to each other:
```markdown
### Advocate Response
[Address concerns, strengthen arguments]

### Critic Response
[Address rebuttals, raise new concerns]

### Pragmatist Response
[Reality check on both sides]
```

#### Round 3: Convergence
Work toward consensus:
```markdown
### Points of Agreement
- [Agreed point 1]
- [Agreed point 2]

### Remaining Disagreements
- [Disagreement 1]
- [Disagreement 2]

### Proposed Resolution
[Synthesized approach]
```

## Output

```markdown
## Debate Conclusion: [Topic]

### Decision
[Final recommendation]

### Rationale
[Why this was chosen]

### Acknowledged Risks
- [Risk 1 and mitigation]
- [Risk 2 and mitigation]

### Dissenting Views
[Any unresolved disagreements]
```

## Best Practices

- Keep rounds focused
- Require evidence for claims
- Drive toward actionable conclusion
- Document minority opinions
