# Text Editor

Provide an LLM-friendly file editing tool for reading, writing, and patching text files.

## What It Does

This plugin exposes a native text editing tool that agents can use to inspect files, write complete contents, and apply validated patch operations while tracking file freshness between reads and edits.

## Main Behavior

- **Read**
  - Reads whole files or line ranges with token-aware limits.
  - Records file metadata so later patch operations can detect stale edits.
- **Write**
  - Writes full file contents and then re-reads the resulting file for confirmation.
- **Patch**
  - Validates edit structures before applying them.
  - Rejects edits if the file changed since it was last observed.
  - Reads back the affected patch region after applying changes.
- **Extension hooks**
  - Exposes before and after extension points for read, write, and patch operations.

## Key Files

- **Tool**
  - `tools/text_editor.py` implements method dispatch, stale-file checks, patching flow, and prompt responses.
- **Helpers**
  - `helpers/file_ops.py` provides file info, read/write helpers, edit validation, and patch application.
- **Configuration**
  - `default_config.yaml` defines read limits and token budgets.
- **Prompts**
  - `prompts/` contains the agent-facing success and error messages.

## Configuration Scope

- **Settings section**: `agent`
- **Per-project config**: `true`
- **Per-agent config**: `true`

## Plugin Metadata

- **Name**: `_text_editor`
- **Title**: `Text Editor`
- **Description**: Native tool to read, write, and patch text files in an LLM-friendly way.
