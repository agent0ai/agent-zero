# LibreOffice Plugin DOX

## Purpose

- Own ODF-first LibreOffice office artifact workflows for Writer, Calc, and Impress files.

## Ownership

- `tools/office_artifact.py` owns the agent-facing office artifact tool.
- `helpers/` owns artifact editing, canvas context, document storage, LibreOffice runtime, and presentation writing.
- `api/` owns office session and WebSocket handlers.
- `hooks.py`, `prompts/`, `skills/`, `extensions/`, and `webui/` own lifecycle behavior, prompts, skill guidance, hooks, and office panel UI.

## Local Contracts

- Preserve document storage integrity and live session synchronization.
- Atomic writes preserve the existing file mode and owner/group; Rename and Save As inherit them from the source. Temporary files and new files from atomic writes start private (0600). Metadata failures must leave the original untouched.
- Version backups use private files (0600) inside a process-owned private directory (0700); `ensure_dirs` also restricts existing backup directories.
- Keep LibreOffice operations bounded to intended workspaces and artifact paths.
- Route APT commands through `system_packages.run_runtime_apt`; Kali repairs must use the build's snapshot when resolving LibreOffice/UNO dependencies.
- Do not expose document contents or temporary files beyond intended UI/tool flows.
- Text registration and Editor writes use FileBrowser-owned text constraints (size, binary content, UTF-8); do not define an independent Editor limit. Office template formats remain unchanged. Only explicit authenticated Editor/File Browser operations opt into filesystem-root paths; default artifact paths stay workspace-scoped.
- Editor text Save As storage helpers must preserve exact UTF-8 text for arbitrary text/code filenames and create a new registered document without mutating or deleting the source document.

## Work Guidance

- Coordinate tool, session, and panel changes so canvas state reflects document state.

## Verification

- Smoke-test creating, editing, previewing, and reconnecting office artifact sessions after changes.

## Child DOX Index

No child DOX files.
