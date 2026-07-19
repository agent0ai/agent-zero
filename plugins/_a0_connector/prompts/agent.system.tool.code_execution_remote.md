# code_execution_remote tool

Runs shell-backed execution on the machine where a connected A0 CLI is running.
Use this tool, not `code_execution_tool`, when the user asks for the connected
local terminal, the A0 CLI host, their local machine, or explicitly says not to
use Docker/server/container execution.
For complex local project work, optionally load skill `host-code-execution`.

Availability and permissions are checked when the tool runs. If no CLI is
connected, remote execution is disabled, or local access is not Read&Write for a
mutating command, report that to the user instead of falling back to server-side
execution.

Do not use this tool as a fallback for host-browser navigation/control. For
"my browser", host browser, local browser/Chrome, or opening a URL in the host
browser, use the `browser` tool. If Browser reports missing Chrome
remote-debugging consent, tell the user to open `chrome://inspect/#remote-debugging`,
enable "Allow remote debugging for this browser instance", run `/browser host on`,
and retry.

## Arguments
- `runtime`: one of `terminal`, `python`, `nodejs`, `output`, `reset`
- `session`: integer session id (default `0`)

Runtime-specific fields:
- `terminal`, `python`, `nodejs`: require `code`
- `reset`: optional `reason`

## Notes
- Reuse `session` when continuing a workflow.
- Use `output` to poll a running session and `reset` for a stuck session.
- Paths and shell syntax are evaluated on the CLI host, not inside Agent Zero.
- When the user gives a relative path like `tmp/file.txt`, keep it relative to
  the CLI host terminal. Do not prepend or `cd` to `/a0/usr/workdir`; that is the
  Agent Zero server/Docker workdir, not the connected local terminal folder.
- If the current terminal folder matters, run `pwd` first or include `pwd` in
  the same command without changing directories.

## Usage
~~~json
{
  "thoughts": [
    "The user asked for the connected local terminal rather than Docker, so I should execute on the A0 CLI host."
  ],
  "headline": "Running command on connected local terminal",
  "tool_name": "code_execution_remote",
  "tool_args": {
    "runtime": "terminal",
    "session": 0,
    "code": "pwd"
  }
}
~~~
