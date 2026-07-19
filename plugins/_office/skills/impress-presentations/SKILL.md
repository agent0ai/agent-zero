---
name: impress-presentations
description: Use when creating, opening, or editing LibreOffice Impress ODP presentations, or PPTX decks only when PowerPoint compatibility is explicitly required.
version: "1.1.0"
author: "Agent Zero Core Team"
tags: ["presentation", "odp", "opendocument", "pptx", "powerpoint", "slides", "deck", "impress"]
triggers:
  - "Impress"
  - "ODP"
  - "odp"
  - "OpenDocument Presentation"
  - "PowerPoint"
  - "PPTX"
  - "pptx"
  - "presentation"
  - "slide deck"
  - "slides"
  - "deck"
  - "Impress"
allowed_tools:
  - document_artifact
---

# Impress Presentations

Use ODP when the user asks for a presentation, slides, a deck, or an Impress artifact. Use PPTX only when the user asks for PowerPoint/PPTX compatibility or provides an existing `.pptx`.

The document UI and Desktop are user-owned. Creating or editing an ODP or PPTX must save the deck, but must not open a document modal or Desktop surface automatically. Use Desktop/Impress only for explicit GUI requests, visual layout polish, or final visual confirmation. Do not write faux UI action labels such as "Open document" or "Download file", and do not add a note saying the canvas was not opened automatically unless the user explicitly asks about UI behavior.

## Workflow

Create:

```json
{
  "tool_name": "document_artifact",
  "tool_args": {
    "action": "create",
    "kind": "presentation",
    "title": "Roadmap",
    "format": "odp",
    "content": "Title Slide\n\n---\n\nNext Steps"
  }
}
```

Edit slides:

```json
{
  "tool_name": "document_artifact",
  "tool_args": {
    "action": "edit",
    "file_id": "abc123",
    "operation": "set_slides",
    "slides": [
      {"title": "Now", "bullets": ["Stabilize"]},
      {"title": "Next", "bullets": ["Polish"]}
    ]
  }
}
```

Practical rules:

- Use `slides` arrays for structured decks and `---` separators for simple text-to-slide creation.
- Keep slide text concise and scannable.
- Treat PPTX as a compatibility export/request, not the default presentation format.
- Do not open Impress/Desktop automatically. The user can choose Open in Desktop when they want to inspect or polish the deck visually.
