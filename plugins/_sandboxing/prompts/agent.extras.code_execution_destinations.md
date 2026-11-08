## Code execution destinations

`code_execution_tool` uses `destination=default` when omitted. Keep the same destination for a session's command, input, output polling, and reset calls.

Available destinations:
{{destinations}}

Use `default` for ordinary commands so work stays isolated. Use `local` only when the task must inspect or modify Agent Zero itself or its core operating system. A stopped or missing sandbox is woken or created automatically.
