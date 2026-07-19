---
name: writer-documents
description: Use when creating, opening, or editing LibreOffice Writer ODT documents, or DOCX documents only when Microsoft Word compatibility is explicitly required.
version: "1.1.0"
author: "Agent Zero Core Team"
tags: ["writer", "odt", "opendocument", "word", "docx", "documents", "reports", "memos", "contracts"]
triggers:
  - "Writer"
  - "ODT"
  - "odt"
  - "OpenDocument Text"
  - "Word"
  - "DOCX"
  - "docx"
  - "Microsoft Word"
  - "LibreOffice Writer"
  - "Word document"
allowed_tools:
  - document_artifact
---

# Writer Documents

Use ODT for LibreOffice Writer documents. Use DOCX only when the user explicitly asks for Word/DOCX/OOXML compatibility, provides an existing `.docx`, or needs that compatibility format. For ordinary writing with no binary requirement, use Markdown instead.

The document UI and Desktop are user-owned. Creating or editing an ODT or DOCX must save the file, but must not open a document modal or Desktop surface automatically. Use Desktop/Writer only for explicit GUI requests, visual layout polish, or final visual confirmation. Do not write faux UI action labels such as "Open document" or "Download file", and do not add a note saying the canvas was not opened automatically unless the user explicitly asks about UI behavior.

## Workflow

Create:

```json
{
  "tool_name": "document_artifact",
  "tool_args": {
    "action": "create",
    "kind": "document",
    "title": "Board Memo",
    "format": "odt",
    "content": "Memo body text."
  }
}
```

Edit:

1. Use the `read` action with `file_id` or `path` before content-sensitive edits.
2. Use the `edit` action for deterministic saved changes: `set_text`, `append_text`, `prepend_text`, `replace_text`, or `delete_text`.
3. Use the Desktop only when the user asks to see Writer or when layout cannot be handled reliably through structured edits.

Practical rules:

- Keep Writer content clean and structured. Use headings and paragraphs; avoid over-formatting unless requested.
- Treat DOCX as a compatibility export/request, not the default Writer format.
- Do not say the document is open. Say it was created or updated, and rely on the Open in Desktop action for user-controlled viewing.
