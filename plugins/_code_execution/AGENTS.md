# Code Execution Plugin DOX

## Purpose

- Own terminal, Python, and Node.js code execution through destination-aware persistent sessions.

## Ownership

- `tools/` owns the code execution and input tools.
- `helpers/` owns local shell and TTY session management.
- `prompts/` owns execution prompt and runtime response fragments.
- `default_config.yaml`, `plugin.yaml`, `extensions/`, and `webui/` own settings, metadata, hooks, and UI config.

## Local Contracts

- Connected-host commands and input use the shared tools with `destination=host`, the connector permissions, and the bundled terminal policy. Only the input wrapper can set `allow_running`.

- Local workdir creation resolves development paths with `files.fix_dev_path`. Local and sandbox sessions share terminal output cleaning in `helpers.strings.clean_string`. Honor a saved or environment-configured legacy SSH selection by declining local execution until the old selection is cleared.

- `extensions/webui/get_process_step_types/code-exe-types.js` registers `code_exe` as a process-step type so raw-log grouping matches the plugin's message renderer.
- Keep command previews compact in rendered execution output. `code-exe-handler.js` restores a matching command prefix from the already-masked `kvps.code` for Copy Output and step details, preserving command whitespace and the output body. Existing log size limits remain; copying cannot recover text already discarded by those limits.
- Normalize logged `code` to display text before title and copy operations. Rejected malformed arguments can remain in stored logs; streaming and replay must render them without changing the original arguments.

- Keep session concurrency, timeout, streaming, and reset behavior predictable.
- Execution runtimes (`terminal`, `python`, `nodejs`) require a string `code` argument. Reject missing or non-string code with `RepairableException` before configuring or resetting shells; output polling and reset do not require code. Verify with `tests/test_code_execution_arguments.py`.
- A direct parallel code job retains its worker and loop-bound shell until the command ends or is cancelled. Output timeouts publish model-facing progress to the registered job and continue polling; callers use parallel job IDs. Close parallel shells explicitly on that worker loop on completion or cancellation, including partially connected shells. Top-level sessions retain their ordinary timeout/output/reset behavior.
- Execute multi-line terminal input as one current-shell compound so intermediate prompts cannot mark queued work complete; preserve `cd`, exports, and other shell state.
- Treat shell exit as command completion even when no final prompt appears. Recreate a terminated session before its next command.
- Terminal reset/close must not hang on foreground commands or shells that ignore SIGTERM.
- POSIX PTY I/O is nonblocking. The existing write/drain interface buffers partial writes and yields while the terminal is full; cancellation discards the shell only while POSIX input bytes remain unsent. Fully drained sends retain the shell and its state.
- TTY destruction uses best-effort kill, never nested event-loop execution; explicit close retains awaited cleanup.
- Windows cleanup uses the native process methods without looking up POSIX-only signals; the pywinpty adapter passes SIGTERM for forced termination. POSIX close retains process-group TERM-then-KILL escalation.
- Local sessions must synchronously release their owned process when discarded.
- The `input` tool logs a prefix-free `icon://keyboard Using tool 'input'` heading and forwards keyboard input through the code execution tool and its log.
- The tool's `allow_running` flag is framework-set (for example by the `input` tool's terminal dispatch); it is not a model-facing arg and stays undocumented in prompts.
- Keep `destination=default` isolated through registered destination extensions. Guide ordinary work to a sandbox and reserve `local` for tasks requiring direct access to the running framework or its operating system. Connected-host routing reuses the authenticated connector transport.
- Key persistent sessions by destination and session id so output, input, and reset cannot cross execution boundaries.
- Do not hardcode secrets or local user paths.
- Direct local POSIX Python snippets run IPython with the framework's `sys.executable`; Windows and sandbox sessions use the target's `ipython` command.

## Work Guidance

- Preserve long-running command output retrieval and busy-session guards when changing execution flow.

## Verification

- Smoke-test terminal, Python, Node.js, output polling, and reset paths after tool changes.
- Run `pytest tests/test_webui_plugin_process_types.py -q` for compact execution previews, full stored command copying, and streamed action updates.

## Child DOX Index

No child DOX files.
