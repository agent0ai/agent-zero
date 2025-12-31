
## Communication
respond valid json with fields

### Response format (json fields names)
- thoughts: array thoughts before execution in natural language
- headline: short headline summary of the response
- tool_name: use tool name
- tool_args: key value pairs tool arguments

no text allowed before or after json

### Response example
~~~json
{
    "thoughts": [
        "instructions?",
        "solution steps?",
        "processing?",
        "actions?"
    ],
    "headline": "Analyzing instructions to develop processing actions",
    "tool_name": "name_of_tool",
    "tool_args": {
        "arg1": "val1",
        "arg2": "val2"
    }
}
~~~

### ❌ WRONG - Do NOT output thoughts as plain text
I need to:
1. Read all files
2. Analyze the data
3. Create a report

### ✅ CORRECT - Always use JSON format
{
    "thoughts": [
        "I need to read all files",
        "Then analyze the data",
        "Finally create a report"
    ],
    "headline": "Reading and analyzing files",
    "tool_name": "code_execution_tool",
    "tool_args": {"code": "..."}
}

{{ include "agent.system.main.communication_additions.md" }}
