# Search Engine Plugin DOX

## Purpose

- Own web-search skill discovery and saved search-message presentation.

## Ownership

- `skills/web-search/SKILL.md` owns agent-facing CLI usage and first-use/status guidance.
- `extensions/webui/` preserves presentation of historical `search_engine` tool logs.
- `plugin.yaml`, `README.md` and `webui/thumbnail.jpg` own catalog metadata and artwork.

## Local Contracts

- Search is a skill plus CLI, not a dedicated tool. Do not register `search_engine` Python tools or system tool prompts.
- The skill invokes `python -m plugins._searxng.search` in the local outer environment. The SearXNG plugin owns all sandbox setup, locking, status and queries through the shared sandbox API.
- Keep first-use notices, waiting/polling instructions, JSON results and upstream error guidance aligned with the CLI.
- Preserve legacy `search_engine` log/process-type renderers for saved conversations.

## Work Guidance

- Keep skill metadata concise and searchable for plain web research; route rendered/interactive pages to Browser.
- Maintain relative links to the CLI and use Linux command examples.

## Verification

- Run `tests/test_search_cli.py`, `tests/test_searxng_plugin.py`, and skill discovery/runtime tests.
- Verify neither the tool catalog nor Responses schemas expose `search_engine`.

## Child DOX Index

No child DOX files.
