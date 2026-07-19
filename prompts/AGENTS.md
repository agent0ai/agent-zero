# Prompts DOX

## Purpose

- Own core prompt templates used by agents, tools, framework messages, behavior updates, summaries, skills, projects, and system context.
- Keep prompt contracts explicit and synchronized with code that renders them.

## Ownership

- `agent.*.md` and companion `.py` files provide system, context, tool, project, skill, and behavior prompt material.
- `fw.*.md` files provide framework-generated message templates.
- Profile-specific prompt overrides belong under `agents/<profile>/prompts/`.
- Plugin prompt additions belong under the relevant plugin `prompts/` directory.

## Local Contracts

- Do not include secrets, real API keys, or private user data in prompt templates.
- Keep placeholder names, include aliases, and template assumptions synchronized with prompt-loading code and extensions.
- Prompt changes can alter agent behavior; keep edits narrow and intentional.
- Maintain clear separation between core behavior prompts and profile/plugin-specific customization.
- Summary prompts that compress history should preserve loaded skill names from `skill_instructions` metadata without copying full skill bodies.

## Work Guidance

- Read the rendering path before changing placeholders or filenames.
- Prefer small prompt additions over broad rewrites when fixing a specific behavior.
- Keep document/OCR routing explicit: image files, screenshots, scans, charts, photos, and diagrams should prefer vision tools when available, while `document_query` is for documents, large text-heavy files, and fallback OCR.
- Update tests or snapshots when prompt budget, required sections, or generated system content changes.

## Verification

- Run targeted prompt, budget, snapshot, tool, or behavior tests after prompt changes.
- Inspect rendered prompt output when changing template wiring or placeholders.

## Child DOX Index

No child DOX files.
