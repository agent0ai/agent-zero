# Code Execution Plugin DOX

## Purpose

- Own terminal, Python, and Node.js code execution through persistent local or SSH-backed sessions.

## Ownership

- `tools/` owns the code execution and input tools.
- `helpers/` owns local shell, SSH shell, and TTY session management.
- `prompts/` owns execution prompt and runtime response fragments.
- `default_config.yaml`, `plugin.yaml`, `extensions/`, and `webui/` own settings, metadata, hooks, and UI config.

## Local Contracts

- Keep session concurrency, timeout, streaming, and reset behavior predictable.
- Execute multi-line terminal input as one current-shell compound so intermediate prompts cannot mark queued work complete; preserve `cd`, exports, and other shell state.
- Terminal reset/close must not hang on foreground commands or shells that ignore SIGTERM.
- Explicitly target local versus SSH execution runtimes.
- Do not hardcode secrets, SSH credentials, or local user paths.

## Work Guidance

- Preserve long-running command output retrieval and busy-session guards when changing execution flow.

## Verification

- Smoke-test terminal, Python, Node.js, output polling, and reset paths after tool changes.

## Child DOX Index

No child DOX files.
