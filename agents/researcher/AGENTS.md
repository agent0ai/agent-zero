# Researcher Agent Profile DOX

## Purpose

- Own the bundled research, data analysis, and reporting specialist profile.
- Keep evidence-gathering and report-oriented behavior separate from general defaults.

## Ownership

- `agent.yaml` owns title, description, and delegation context for research work.
- `prompts/` owns researcher-specific prompt overrides when present.

## Local Contracts

- Keep this profile focused on information gathering, analysis, synthesis, and reporting.
- Do not bake in project-specific sources, credentials, or local paths.
- Preserve the framework tool-call and response contracts.

## Work Guidance

- Prefer prompt changes that improve citation, evidence handling, and analysis quality for research tasks.
- Coordinate broad research behavior changes with document or browser plugin contracts when relevant.

## Verification

- Manually inspect `agent.yaml` for valid YAML after edits.
- Run prompt/profile tests when changing discovery or researcher prompt behavior.

## Child DOX Index

No child DOX files.
