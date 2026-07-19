---
name: calc-spreadsheets
description: Use when creating, opening, or editing LibreOffice Calc ODS spreadsheets, or XLSX workbooks only when Excel compatibility is explicitly required.
version: "1.1.0"
author: "Agent Zero Core Team"
tags: ["calc", "ods", "opendocument", "excel", "xlsx", "spreadsheet", "workbook", "tables", "charts", "budget"]
triggers:
  - "Calc"
  - "ODS"
  - "ods"
  - "OpenDocument Spreadsheet"
  - "Excel"
  - "XLSX"
  - "xlsx"
  - "spreadsheet"
  - "workbook"
  - "budget"
  - "sheet"
  - "chart"
allowed_tools:
  - document_artifact
---

# Calc Spreadsheets

Use ODS when the user asks for a spreadsheet, workbook, editable table, budget, formulas, or Calc file. Use XLSX only when the user asks for Excel/XLSX compatibility, provides an existing `.xlsx`, or needs embedded spreadsheet charts supported by the tool.

The document UI and Desktop are user-owned. Creating or editing an ODS or XLSX must save the workbook, but must not open a document modal or Desktop surface automatically. Use Desktop/Calc only for explicit GUI requests, visual chart/layout polish, or final visual confirmation. Do not write faux UI action labels such as "Open document" or "Download file", and do not add a note saying the canvas was not opened automatically unless the user explicitly asks about UI behavior.

## Workflow

Create a workbook:

```json
{
  "tool_name": "document_artifact",
  "tool_args": {
    "action": "create",
    "kind": "spreadsheet",
    "title": "Budget",
    "format": "ods",
    "content": "Item,Amount\nPlatform,1000"
  }
}
```

For a blank workbook request, create a simple workbook with the requested title and `format: "ods"`; do not call `status` first unless the user asked for availability.

Edit cells:

```json
{
  "tool_name": "document_artifact",
  "tool_args": {
    "action": "edit",
    "file_id": "abc123",
    "operation": "set_cells",
    "cells": {
      "Sheet1!A1": "Item",
      "Sheet1!B1": "Amount"
    }
  }
}
```

Practical rules:

- `content` may be CSV, TSV, or a Markdown table; the tool writes real spreadsheet cells.
- Use `rows` for whole-table replacement, `append_rows` for adding records, and `set_cells` for precise edits.
- Use `create_chart` with a chart object for embedded charts when working in XLSX compatibility format; otherwise use Calc/Desktop or code execution for chart workflows that ODS direct editing does not yet cover.
- Do not open Calc/Desktop automatically. The user can choose Open in Desktop when they want the visible spreadsheet.
