### run_task Tool

## Description
The `run_task` tool executes other tools in isolated background contexts.

#### Batched Tool Calls (required)
- Use `tool_calls` to pass a JSON object mapping `call_id` to a tool call object
- Each `call_id` must be a non-empty string with no whitespace characters
- Each tool call object must include:
  - `tool_name` (required): Name of the tool to execute
  - `method` (optional): Method to call on the tool
  - `args` (optional): Object or JSON string of arguments for the tool
  - `message` (optional): Message context for the tool
- The tool starts all calls and returns a mapping from `call_id` to task UUID or an error string
- Response format: one pair per line as `call_id: <uuid>` or `call_id: Error: <text>`

##### Example
```json
{
  "tool_name": "run_task",
  "tool_args": {
    "tool_calls": "{\"search1\": {\"tool_name\": \"search_engine\", \"method\": \"search\", \"args\": {\"query\": \"vector databases\"}}, \"code1\": {\"tool_name\": \"code_exe\", \"method\": \"execute\", \"args\": {\"language\": \"python\", \"code\": \"print('hi')\"}} }"
  }
}
```

#### Behavior
- Each task runs in an isolated temporary BACKGROUND context and is cleaned up after completion
- Results are stored and can be retrieved later with `wait_for_tasks`
- On input or runtime error for a call, the returned value is `Error: <text>` for that `call_id`

#### Notes
- Avoid whitespace in `call_id` (no spaces, tabs, or newlines)
- Prefer batching independent tool invocations to reduce overhead
- Use `wait_for_tasks` with task IDs returned in the response to collect results
