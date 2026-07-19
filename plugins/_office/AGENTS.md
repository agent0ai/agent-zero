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
- Keep LibreOffice operations bounded to intended workspaces and artifact paths.
- Do not expose document contents or temporary files beyond intended UI/tool flows.
- Editor text Save As storage helpers must preserve exact `.md` or `.txt` text and create a new registered document without mutating or deleting the source document.

## Work Guidance

- Coordinate tool, session, and panel changes so canvas state reflects document state.

## Verification

- Smoke-test creating, editing, previewing, and reconnecting office artifact sessions after changes.

## Child DOX Index

No child DOX files.
