### call_subordinate

**When to Use This Tool:**

Before calling this tool, evaluate these questions in your thoughts:

1. **Subtask Boundary Check**: Is this a distinct, self-contained subtask with clear inputs/outputs, or is it essentially the full task I was assigned?
2. **Context Efficiency Check**: Will delegating this subtask clear my context and let me focus on coordination, or am I just offloading my core responsibility?
3. **Specialization Check**: Does this require specialized capabilities (different profile) or tools I don't have access to, or can I handle it directly?

**Delegation Decision**: Delegate ONLY if at least 2 of these checks favor delegation.

**Critical Rules:**

- NEVER delegate your full/core task to a subordinate with the SAME profile as you (e.g., developer → developer with same task). This creates infinite loops.
- You CAN delegate your full task to a DIFFERENT specialized profile (e.g., default → developer, researcher → developer)
- Delegate specific subtasks, not entire problems
- If you can solve it with your available tools, do it yourself

**Anti-Patterns (DO NOT DO THIS):**

- Don't delegate the entire task to a subordinate with your same profile
- Don't delegate just to avoid thinking through the problem
- Don't delegate if you can use a tool directly
- Don't delegate trivial tasks that take less effort to do than to explain

**Profile Selection:**

- Use `profile` arg to select specialized subordinates (scientist, coder, engineer, etc.)
- Leave `profile` empty ONLY when delegating to a general-purpose agent
- Match the profile to the task: coding → coder, research → scientist, etc.

**Arguments:**

- `message`: Always describe role, task details, goal overview for new subordinate
- `reset`: "true" to spawn new subordinate, "false" to continue existing subordinate
- `profile`: Select from available profiles for specialized subordinates, leave empty for default

**Example Usage:**

~~~json
{
    "thoughts": [
        "Subtask Boundary Check: This is a specific code implementation subtask, not my core orchestration task - YES",
        "Context Efficiency Check: Delegating this lets me focus on overall architecture - YES",
        "Specialization Check: I need coder profile for implementation - YES",
        "2+ checks favor delegation, and I'm using a DIFFERENT profile (coder), so delegation is appropriate"
    ],
    "tool_name": "call_subordinate",
    "tool_args": {
        "profile": "coder",
        "message": "Implement the user authentication module with JWT tokens. Requirements: ...",
        "reset": "true"
    }
}
~~~

**Response Handling:**

- You might be part of long chain of subordinates
- Avoid slow and expensive rewriting subordinate responses
- Instead use `§§include(<path>)` alias to include the response as is

**Available Profiles:**
{{agent_profiles}}
