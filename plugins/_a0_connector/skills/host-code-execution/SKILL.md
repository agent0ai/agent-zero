---
name: host-code-execution
description: Guide safe use of code_execution_remote for shell-backed execution on the connected A0 CLI host. Use when the user asks for their computer, local terminal, CLI host, remote shell, not Docker, or host-side Python/Node/terminal commands.
---

# Host Code Execution

## Boundary

Use `code_execution_remote` only for shell-backed execution on the machine where A0 CLI is running. Shells, runtimes, and paths belong to the CLI host, not the Agent Zero server or Docker container.

If the task belongs inside Agent Zero's own runtime, use the normal server-side execution tool instead.

Browser boundary: do not use shell launchers such as `xdg-open`, `sensible-browser`, `open`, `start`, or Python `webbrowser.open` as a fallback for requests to use/control/open a page in the host browser. Use the `browser` tool instead; if it reports missing Chrome remote-debugging consent, stop and relay the `chrome://inspect/#remote-debugging` instructions.

## Access Modes

- Remote execution can be disabled locally in the CLI. If the tool returns a disabled/no-client error, explain the required CLI toggle instead of falling back to the server runtime.
- Read&Write local file access allows mutating runtimes such as `terminal`, `python`, and `nodejs`.
- Read only local file access blocks mutating runtimes. `runtime=output` and `runtime=reset` remain available for existing sessions.

## Runtimes

- Use `runtime=terminal` for shell commands, `runtime=python` for Python snippets, and `runtime=nodejs` for Node.js snippets.
- Reuse the same integer `session` while continuing a workflow; session state is local to the CLI frontend.
- Use `runtime=output` when a previous command is still running or returned before the shell reached a prompt.
- Use `runtime=reset` when a session is stuck and no replacement command needs to run yet.
- Use `reset: true` with `runtime=terminal`, `python`, or `nodejs` when a session is stuck and the next command should run immediately in a clean shell.
- Match the remote host shell syntax. A Windows CLI may need PowerShell syntax even when Agent Zero runs on Linux.

## Failure Handling

- If no CLI is connected, ask the user to connect A0 CLI to this Agent Zero instance.
- If execution is disabled, tell the user to enable remote execution in the CLI.
- If mutating runtimes are blocked, tell the user to switch local file access to Read&Write with F3.
- If a request times out or the CLI disconnects, poll once if a session may still be running; otherwise summarize the failure and wait for reconnection.
