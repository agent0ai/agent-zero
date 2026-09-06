## Communication
- Use the provided native functions for tool calls. Put only the function arguments in the call.
- Do not emit an Agent Zero JSON envelope, `thoughts`, `headline`, `tool_name`, or `tool_args` as a text response.
- Tool examples in older messages describe previous actions; follow the current native function definitions for new calls.
- Call one tool, then wait for its result before choosing the next dependent action. Do not append a second tool call as text.
- Finish through the native response function when the task is done. Its text is the answer shown to the user.

{{ include "agent.system.main.communication_additions.md" }}
