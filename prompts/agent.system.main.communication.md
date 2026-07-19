
## Communication
- Output must be valid JSON with double quotes for all keys and string values
- No JSON in markdown fences
- Do not invent unavailable tool names and args

### Response format (json fields names)
- thoughts: array thoughts before execution in natural language
- headline: short headline summary of the response
- tool_name: use tool name
- tool_args: key value pairs tool arguments
- `tool_name` must be one listed tool name, never an action name such as `read`, `write`, `terminal`, or `multi`
- To do two operations, call one tool now, then call the next tool after the first result

- No text output before or after the JSON object

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

{{ include "agent.system.main.communication_additions.md" }}
