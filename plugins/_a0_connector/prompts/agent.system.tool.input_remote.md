### input_remote
send keyboard input to an interactive program on the connected CLI host
args: `keyboard`, optional `session` (default `0`)
enabled by default; explicit tool policies must allow `input_remote` and the `terminal` action of `code_execution_remote`, because keyboard input can run shell commands
uses the same connection and Read&Write gates as `code_execution_remote`
for Agent Zero's own terminal, use `input`; for host browser actions, use `browser`
usage:
~~~json
{
  "tool_name": "input_remote",
  "tool_args": {
    "keyboard": "Y",
    "session": 0
  }
}
~~~
