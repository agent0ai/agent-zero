# Attachment Preview

Inline preview panel for chat attachments and workdir file links — supports images, PDF, video, audio, markdown, HTML, and source code.

## What It Does

This plugin adds a split-screen preview panel below the chat area. Clicking a previewable attachment chip or a workdir file link in agent messages opens the file directly inside the UI instead of downloading or navigating away.

## Main Behavior

- **Attachment chips**
  - Intercepts clicks on non-image attachment chips in the chat input area.
  - Routes to the preview panel if the file extension is supported.
- **Workdir links**
  - Overrides `openFileLink()` to preview files linked in agent messages (`<a onclick="openFileLink(...)">`).
  - Intercepts `<a href="/api/download_work_dir_file?...">` links in chat history via delegated click handler.
- **Preview routing**
  - Images → `/api/image_get` (reuses core API).
  - Markdown / text / code → `/api/edit_work_dir_file` (fetches content, renders markdown with safe renderer).
  - HTML / PDF / video / audio → `/api/plugins/_attachment_preview/preview_work_dir_file` (streams file inline with appropriate Content-Type).
- **Panel features**
  - Vertical split layout with drag-to-resize handle.
  - Maximize to 80% centered overlay with blur backdrop.
  - Download button for saving the previewed file.

## Key Files

- **API**
  - `api/preview_work_dir_file.py` streams files inline with CSP sandbox for HTML. Handles both Docker and development environments.
- **Frontend**
  - `webui/preview-store.js` is the Alpine.js store (`attachmentPreview`) managing state, file type routing, resize, and maximize logic.
  - `extensions/webui/right-panel-after-chat/preview-panel.html` is the panel component with inlined CSS, loaded via the `right-panel-after-chat` extension point.

## Core File Modifications

- `webui/index.html` — Added `<x-extension id="right-panel-after-chat">` between chat area and toast.
- `webui/components/chat/attachments/attachmentsStore.js` — Added loose-coupled preview calls via `Alpine.store('attachmentPreview')`.

## Plugin Metadata

- **Name**: `_attachment_preview`
- **Title**: `Attachment Preview`
- **Description**: Inline preview panel for attachments - supports PDF, text, code, video, audio, markdown, and HTML files.
- **Always enabled**: `true`
