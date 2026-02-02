### claude_code:

ALWAYS use this tool for ANY coding task - writing code, debugging, refactoring, code review, implementation, fixing errors
DO NOT attempt to write code yourself - delegate ALL coding to Claude Code CLI
This tool has superior coding capabilities and MUST be used for any programming task

**arguments:**
- task: (required) detailed description of the coding task
- working_dir: (optional) directory to run claude in

usage:

~~~json
{
    "thoughts": ["This is a coding task", "I MUST delegate to Claude Code"],
    "headline": "Delegating to Claude Code",
    "tool_name": "claude_code",
    "tool_args": {
        "task": "Write a Python hello world script"
    }
}
~~~
