---
name: host-file-editing
description: Guide safe use of text_editor_remote for reading, writing, and patching files on the connected A0 CLI host. Use when the user asks to inspect or edit files on their computer, local files, CLI host files, or files that are explicitly not Docker/server files.
---

# Host File Editing

## Boundary

Use `text_editor_remote` only for file work on the machine where A0 CLI is running. These paths and files belong to the CLI host, not the Agent Zero server or Docker container.

If the task belongs inside Agent Zero's own runtime, use the normal server-side file tools instead.

## Access Modes

- Read&Write: reads, writes, and patches may modify the CLI host. Keep changes narrow and intentional.
- Read only: inspect files only. If writes are blocked, tell the user to switch local file access to Read&Write with F3.

## Editing Flow

- Start with `read` when inspecting a file or preparing line-based edits.
- Use `write` only when replacing or creating the whole file is truly the right operation.
- Prefer `patch` with `old_text` and `new_text` for simple exact replacements.
- Use `patch_text` for context-anchored edits, especially after inserts/deletes or when line numbers may have shifted.
- Use `patch` with `edits` only for small line-range edits based on the latest remote read.
- If freshness-aware line patching rejects an edit as stale, reread the file and retry with updated ranges.
- Treat reads as bounded text previews (2,000 lines / 256 KiB). Follow
  `next_line` for another small slice; use the authenticated HTTP transfer path
  for complete large files and binary data.
- Keep each write or patch payload within 256 KiB. Do not split a binary file
  into text-editor calls.

## Patch Text Rules

- Exact replace requires `old_text` to match one exact current span; use a longer span if it matches multiple places.
- `patch_text` supports update hunks for one file.
- Use one `@@ existing line` anchor, then `+new line` entries for insertion.
- For replacement, use `@@ before target` followed by `-old` and `+new`, or use `@@ old target` followed by the same replacement pair.
- Do not repeat the same old line as both context and deletion in one hunk.
- Every non-header content line must begin with exactly one prefix: space for context, `+` for additions, or `-` for removals.
- Do not stack multiple `@@` anchors for one insert.

## Failure Handling

- If no CLI is connected, ask the user to connect A0 CLI to this Agent Zero instance.
- If writes are blocked, tell the user to switch local file access to Read&Write with F3.
- If a request times out or the CLI disconnects, summarize the failure and wait for reconnection.
- If the tool rejects binary or oversized content, use the CLI/Core HTTP
  upload/download path when the workflow exposes it; otherwise ask the user to
  attach or upload the file through A0 CLI.
