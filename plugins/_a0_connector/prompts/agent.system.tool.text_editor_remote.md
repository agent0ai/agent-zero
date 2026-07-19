# text_editor_remote tool

Reads, writes, and patches files on the machine where a connected A0 CLI is
running. Use this tool, not server-side file tools, when the user asks for files
on the connected local machine, A0 CLI host, or explicitly says not to use
Docker/server files. For complex remote edits, optionally load skill `host-file-editing`.

Availability and permissions are checked when the tool runs. If no CLI is
connected, remote file access is disabled, or a write/patch needs Read&Write,
report that to the user instead of falling back to server-side file tools.

## Arguments
- `action`: `read`, `write`, or `patch`
- `path`: file path on the CLI host filesystem
- `read`: optional `line_from`, `line_to`
- `write`: requires `content`
- `patch`: requires one of `old_text` + `new_text`, `patch_text`, or `edits`

## Notes
- Prefer `read` before line-number edits.
- If the user says patch, change without rewriting, or don't rewrite, use `action: "patch"` instead of `write`.
- For simple "change X to Y" requests, prefer exact replace with `old_text` and `new_text`; `old_text` must match one exact current span.
- Prefer `patch_text` for context-anchored changes and `edits` only for fresh, surgical line ranges.
- If freshness checks reject a line patch, reread the file and retry with updated ranges.
- Relative paths are relative to the CLI host filesystem. Do not rewrite them to
  `/a0/usr/workdir`; that path belongs to the Agent Zero server/Docker side.

## Usage
~~~json
{
  "thoughts": [
    "The user asked for a file on the connected local machine, so I should read it through the A0 CLI host."
  ],
  "headline": "Reading file on connected local machine",
  "tool_name": "text_editor_remote",
  "tool_args": {
    "action": "read",
    "path": "README.md",
    "line_from": 1,
    "line_to": 80
  }
}
~~~
