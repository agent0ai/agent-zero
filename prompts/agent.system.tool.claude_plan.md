### claude_plan:

ALWAYS use this tool for ANY planning, architecture, or analysis task
DO NOT attempt to plan or design yourself - delegate ALL planning to Claude Plan CLI
This tool uses extended thinking for deeper reasoning and MUST be used for any strategic decisions

**arguments:**
- task: (required) detailed description of the planning/analysis task
- working_dir: (optional) directory context for file access

usage:

~~~json
{
    "thoughts": ["This requires planning or analysis", "I MUST delegate to Claude Plan"],
    "headline": "Delegating to Claude Plan",
    "tool_name": "claude_plan",
    "tool_args": {
        "task": "Design the architecture for a REST API"
    }
}
~~~
