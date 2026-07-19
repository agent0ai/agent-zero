---
name: document-artifacts
description: Use when creating, opening, reading, or editing editable document artifacts such as Markdown documents, LibreOffice-native ODT/ODS/ODP files, and compatibility DOCX/XLSX/PPTX files with the document_artifact tool.
version: "1.4.0"
author: "Agent Zero Core Team"
tags: ["documents", "markdown", "md", "odt", "ods", "odp", "docx", "xlsx", "pptx", "editor", "spreadsheets", "presentations", "libreoffice", "opendocument"]
triggers:
  - "document artifact"
  - "markdown document"
  - "editable document"
  - "md"
  - "odt"
  - "ods"
  - "odp"
  - "docx"
  - "xlsx"
  - "pptx"
  - "writer"
  - "spreadsheet"
  - "presentation"
allowed_tools:
  - document_artifact
---

# Document Artifacts

Use `document_artifact` for substantial deliverables that should remain editable in the custom document editor or LibreOffice Desktop. Markdown remains the default for ordinary writing, notes, reports, briefs, and drafts when no binary office file is needed. For LibreOffice office files, ODF is first-class: use ODT for Writer, ODS for Spreadsheet/Calc, and ODP for Presentation/Impress. Use DOCX, XLSX, or PPTX only when the user explicitly asks for OOXML compatibility, provides an existing file in that format, or needs that compatibility format.

The document UI and Desktop are user-owned. Creating, reading, or editing an artifact must save the file and update its state, but it must not open a document modal or Desktop surface automatically if the user has not asked for that UI. Use the `open` action, `open_in_canvas: true`, or `open_in_desktop: true` only when the user explicitly asks to open the document/editor/Desktop. After create/edit, answer briefly with what changed and the saved path when useful; do not write faux UI action labels such as "Open document" or "Download file", and do not add a note saying the canvas was not opened automatically unless the user explicitly asks about UI behavior.

For format-specific work, prefer the matching skill when available:

- `markdown-documents` for Markdown-first editable writing.
- `writer-documents` for Writer/ODT files and DOCX compatibility files.
- `calc-spreadsheets` for Calc/ODS spreadsheets and XLSX compatibility workbooks.
- `impress-presentations` for Impress/ODP decks and PPTX compatibility decks.

## Workflow

1. Create or open the artifact with `tool_name: "document_artifact"` and `tool_args.action: "create"` or `"open"`.
2. Before content-sensitive edits, call the `read` action with `file_id` or `path`.
3. Apply saved changes with the `edit` action.
4. Use `version_history` or `restore_version` when the user asks to audit or roll back.

Document context may list opened files with `file_id`, path, version, size, and timestamp. It intentionally omits full file contents; use `read` when the content matters.

## Minimal Calls

Create:
```json
{
  "tool_name": "document_artifact",
  "tool_args": {
    "action": "create",
    "kind": "document",
    "title": "Project Brief",
    "format": "md",
    "content": "Draft text here."
  }
}
```

For spreadsheets, `content` can be CSV, TSV, or a Markdown table; the tool writes real cells, not one text blob per row.

Read:
```json
{
  "tool_name": "document_artifact",
  "tool_args": {
    "action": "read",
    "file_id": "abc123"
  }
}
```

Edit text in a Markdown, ODT, DOCX, ODP, or PPTX file:
```json
{
  "tool_name": "document_artifact",
  "tool_args": {
    "action": "edit",
    "file_id": "abc123",
    "operation": "replace_text",
    "find": "old phrase",
    "replace": "new phrase"
  }
}
```

Append text to a Markdown, ODT, or DOCX file:
```json
{
  "tool_name": "document_artifact",
  "tool_args": {
    "action": "edit",
    "file_id": "abc123",
    "operation": "append_text",
    "content": "\nAdded line 1\nAdded line 2"
  }
}
```

Set spreadsheet cells:
```json
{
  "tool_name": "document_artifact",
  "tool_args": {
    "action": "edit",
    "path": "/a0/usr/workdir/documents/Budget.ods",
    "operation": "set_cells",
    "cells": {
      "Sheet1!B2": 12500,
      "Sheet1!B3": 9800
    }
  }
}
```

Create an embedded spreadsheet chart:
```json
{
  "tool_name": "document_artifact",
  "tool_args": {
    "action": "edit",
    "file_id": "abc123",
    "operation": "create_chart",
    "sheet": "Sheet1",
    "chart": {
      "type": "line",
      "title": "Monthly Revenue",
      "data_range": "B1:C13",
      "categories": "A2:A13",
      "position": "E1",
      "width": 18,
      "height": 10
    }
  }
}
```

## Edit Operations

- MD, ODT, and DOCX: `set_text`, `append_text`, `prepend_text`, `replace_text`, `delete_text`.
- ODS and XLSX: `set_cells`, `append_rows`, `set_rows`, `replace_text`, `delete_text`.
- XLSX only: `create_chart` for embedded spreadsheet charts.
- ODP and PPTX: `set_slides`, `append_slide`, `replace_text`, `delete_text`.

Arguments:

- `set_text`, `append_text`, and `prepend_text` use `content` for the text being written; do not put that text in value, update, or edits.
- `replace_text` and `delete_text` require `find`; `replace_text` uses `replace`.
- `set_cells` accepts `{ "A1": "value", "Sheet2!B3": 42 }` or `[{"sheet":"Sheet1","cell":"A1","value":"value"}]`.
- `rows` accepts an array of rows. `content` can also be CSV, TSV, or a Markdown table.
- `create_chart` accepts `chart` as an object or JSON string for XLSX compatibility workbooks. Supported XLSX chart types: `line`, `bar`, `column`, `pie`, `area`, `scatter`, `stock`, `ohlc`, `candlestick`. Use `data_range`, `categories`/`labels`, `position`, `title`, `width`, and `height`. For stock-style charts only, provide Open/High/Low/Close columns in that order, or rely on a sheet whose headers are `Date, Open, High, Low, Close`.
- `slides` accepts `[{"title":"Slide title","bullets":["point"]}]`. Text slides can be separated with a line containing `---`.
- `count` limits text replacements.

## Practical Rules

- Prefer `file_id` from document context or prior tool output; use `path` when that is all you have.
- Use `read` before editing unless the current saved content is already known.
- Do not create an artifact for tiny one-shot edits or answers the agent can finish cleanly in chat or by directly editing the file.
- For document-style writing requests with no requested binary format, create Markdown and let the custom Markdown editor be the primary interactive editor.
- For spreadsheet or presentation file requests with no OOXML compatibility requirement, create ODS or ODP.
- The Desktop runtime may be warmed during Agent Zero startup, but visible Desktop surface use remains opt-in. Treat LibreOffice GUI work as appropriate for explicit GUI requests, binary Office visual polish, or final layout inspection.
- Never open a document modal or Desktop surface automatically from a tool result. If the user has not opened it, leave the saved artifact available through the normal UI affordance.
- Use native `create_chart` for embedded spreadsheet charts. Reach for Python/code execution only when the requested chart behavior is not supported by the tool.
- Use `edit` for precise saved changes; use the document editor or Desktop for human/manual layout polish.
- Direct edits update version history and refresh the document UI on edit/open results.
