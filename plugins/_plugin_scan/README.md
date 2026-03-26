# Plugin Scanner

Run an LLM-guided security review of third-party Agent Zero plugins from a Git repository.

## What It Does

This plugin builds a structured scanning prompt from a selectable checklist, runs that prompt in a temporary agent context, and returns a markdown report describing the plugin's security posture.

## Main Behavior

- **Prompt-driven scan**
  - Loads scan checks and a markdown prompt template from the plugin's `webui/` assets.
- **Temporary scan context**
  - Creates a temporary chat context, sends the generated prompt as a user message, waits for the model result, and then removes the chat.
- **Selectable checks**
  - Supports scanning all checks by default or only the subset selected by the caller.
- **UI integration**
  - Includes API endpoints and web UI files for queueing, starting, and running scans.

## Key Files

- **Scan runner**
  - `api/plugin_scan_run.py` performs a synchronous end-to-end scan and returns the report.
- **Prompt builder**
  - `helpers/prompt.py` loads check definitions and renders the final scan prompt.
- **Additional APIs**
  - `api/plugin_scan_queue.py`
  - `api/plugin_scan_start.py`

## Configuration Scope

- **Settings sections**: none
- **Per-project config**: `false`
- **Per-agent config**: `false`

## Plugin Metadata

- **Name**: `_plugin_scan`
- **Title**: `Plugin Scanner`
- **Description**: Security scanner for third-party A0 plugins.
