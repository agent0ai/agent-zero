---
name: markdown-documents
description: Use when creating or editing Markdown documents, notes, reports, briefs, drafts, or other editable writing where Markdown should be the primary artifact format.
version: "1.0.0"
author: "Agent Zero Core Team"
tags: ["markdown", "md", "documents", "writing", "notes", "reports", "briefs", "editor"]
triggers:
  - "markdown"
  - "md"
  - "note"
  - "brief"
  - "draft"
  - "report"
  - "editable writing"
allowed_tools:
  - text_editor
---

# Markdown Documents

Markdown is the default document format for normal writing, notes, reports, briefs, drafts, and collaborative text work unless the user explicitly asks for a binary office file. When they do ask for a LibreOffice office file, prefer ODF: ODT for Writer, ODS for Spreadsheet/Calc, and ODP for Presentation/Impress. Use DOCX, XLSX, or PPTX only for explicit OOXML compatibility.

The Editor surface is user-owned UI. Create or update the saved Markdown file, but never open the Editor automatically. Set `open_in_canvas: true` only when the user explicitly asks to open the canvas/Editor; otherwise already-open Editor sessions refresh automatically. Keep the final response to the saved/updated result and path; do not write faux UI action labels such as "Open document" or "Download file", and do not add a note saying the canvas was not opened automatically unless the user explicitly asks about UI behavior.

## Workflow

1. Decide whether a saved editable artifact is useful. Create one for substantial, reusable, or collaborative writing; do not create one for tiny one-shot edits or answers that can be completed cleanly in chat.
2. Create Markdown with `text_editor` using `action: "write"` and an explicit `.md` path.
3. For edits to an existing Markdown file, read first when content matters, then use `patch` for targeted changes or `write` for deliberate full replacement.
4. Report the saved file path briefly. Do not say it was opened unless the user explicitly opened it.

Minimal create:

```json
{
  "tool_name": "text_editor",
  "tool_args": {
    "action": "write",
    "path": "/a0/usr/workdir/Project Brief.md",
    "content": "# Project Brief\n\nDraft text here."
  }
}
```

Practical rules:

- Prefer Markdown over ODT/DOCX for writing unless a binary Writer/Word file is explicitly needed.
- Keep agent-only cleanup simple: if the user asks to fix a typo, update the file and finish; do not force a document-editor workflow.
- Use clear headings and Markdown tables when they improve editability.
- The Markdown Editor surface is available through the response file card.
