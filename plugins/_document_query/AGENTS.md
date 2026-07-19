# Document Query Plugin DOX

## Purpose

- Own document loading, parsing, indexing, and Q&A over local and remote documents.

## Ownership

- `tools/document_query.py` owns the agent-facing query tool.
- `helpers/` owns fetching, parser routing, indexing, and query orchestration.
- `prompts/` owns document-query tool and optimization prompts.
- `hooks.py`, `default_config.yaml`, `plugin.yaml`, `skills/`, `extensions/`, and `webui/` own dependency bootstrap, settings, metadata, skill guidance, hooks, and UI.

## Local Contracts

- Respect configured size, timeout, retry, parser concurrency, and OCR limits.
- Fetch local and remote resources safely and avoid leaking document contents beyond intended prompt/tool use.
- Keep optional dependency installation targeted to the framework runtime.

## Work Guidance

- Coordinate parser changes with timeout handling and fallback behavior.
- Keep prompt and skill guidance clear that image files, screenshots, scans, charts, photos, and diagrams should go to vision tools first when available; `document_query` image OCR is a text-focused fallback when vision is unavailable or cannot read the needed text.

## Verification

- Smoke-test representative PDF, text/HTML, image/OCR, and remote-document queries after parser changes.

## Child DOX Index

No child DOX files.
