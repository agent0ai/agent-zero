# Plugin Validator

Validate Agent Zero plugins against structural, manifest, convention, and security expectations.

## What It Does

This plugin generates a structured validation prompt for either a local plugin or an external source, runs the review in a temporary agent context, and returns a markdown report that checks whether a plugin follows Agent Zero plugin conventions.

## Main Behavior

- **Source-aware validation**
  - Supports validating a local plugin by name or a plugin fetched from a Git repository.
- **Checklist-based review**
  - Loads validation criteria, status icons, and guidance text from plugin assets.
- **Temporary validation context**
  - Creates a temporary agent context, runs the generated prompt, and cleans up the context and temporary chat afterward.
- **Operational guidance in prompt**
  - Embeds source-specific handling instructions into the prompt, including cleanup rules for temporary validation directories.

## Key Files

- **Validation runner**
  - `api/plugin_validator_run.py` performs a synchronous validation and returns the report.
- **Prompt builder**
  - `helpers/prompt.py` builds the validation prompt with source instructions, selected checks, and scoring guidance.
- **Additional APIs**
  - `api/plugin_validator_prepare_zip.py`
  - `api/plugin_validator_queue.py`
  - `api/plugin_validator_start.py`

## Configuration Scope

- **Settings sections**: none
- **Per-project config**: `false`
- **Per-agent config**: `false`

## Plugin Metadata

- **Name**: `_plugin_validator`
- **Title**: `Plugin Validator`
- **Description**: Validate Agent Zero plugins against manifest, structure, code pattern, and security conventions.
