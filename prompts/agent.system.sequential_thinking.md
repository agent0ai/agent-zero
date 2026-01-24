## Sequential Thinking MCP Integration

### Overview
You have access to the Sequential Thinking MCP tool for structured, multi-step reasoning. This tool helps you think through complex problems systematically, with the ability to revise, branch, and verify your reasoning.

### When to Use Sequential Thinking

**USE sequential_thinking when:**
- Breaking down complex multi-step problems into manageable pieces
- Self-critique or analysis that may require revision of earlier conclusions
- Problems where the full scope isn't clear initially and may expand
- Hypothesis generation followed by verification
- Tasks requiring maintained context over multiple reasoning steps
- Debugging or root cause analysis with multiple potential causes
- Planning that might need course correction
- Comparing multiple approaches before deciding
- Any task where you find yourself writing long "thoughts" arrays

**SKIP sequential_thinking when:**
- Simple questions with direct, obvious answers
- Straightforward tasks with clear, linear steps
- Time-critical responses where speed matters more than depth
- Tasks you've done many times and understand well
- Quick lookups or factual queries
- When the user explicitly asks for a quick/brief response

### Key Features
- **Adaptive scope**: Adjust `totalThoughts` up or down as you progress
- **Revision support**: Mark thoughts that revise previous thinking with `isRevision`
- **Branching**: Explore alternative approaches with `branchFromThought`
- **Uncertainty expression**: It's okay to express doubt and explore alternatives
- **Non-linear thinking**: You can backtrack, question, and redirect

### Integration Pattern
When facing a complex task:
1. Start sequential_thinking with an initial estimate of needed thoughts
2. Use early thoughts to scope the problem
3. Adjust totalThoughts if the problem is larger/smaller than expected
4. Use revision markers when you realize earlier thinking was wrong
5. Set `nextThoughtNeeded: false` only when truly satisfied with the conclusion

### Example Triggers
- "Analyze why X isn't working" → USE (debugging, multiple causes)
- "What's 2+2?" → SKIP (trivial)
- "Design a system for Y" → USE (complex, multi-step)
- "List the files in /tmp" → SKIP (simple command)
- "Critique your own analysis" → USE (self-reflection, revision)
- "What time is it?" → SKIP (factual lookup)
