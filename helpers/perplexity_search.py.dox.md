# perplexity_search.py DOX

## Purpose

- Own the `perplexity_search.py` helper module.
- This module queries Perplexity search using configured model/provider credentials.
- Keep this file-level DOX profile synchronized with `perplexity_search.py` because this directory is intentionally flat.

## Ownership

- `perplexity_search.py` owns the runtime implementation.
- `perplexity_search.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Top-level functions:
- `perplexity_search(query: str, model_name=..., api_key=..., base_url=...)`

## Runtime Contracts

- Helper modules own reusable framework APIs and must preserve public callers unless all callers, tests, and docs are updated together.
- Update this file whenever public functions, classes, persistence behavior, path/security assumptions, side effects, or cross-module contracts change.
- Observed side-effect areas: secret handling.
- Imported dependency areas include: `models`, `openai`.

## Key Concepts

- Important called helpers/classes observed in the source: `OpenAI`, `client.chat.completions.create`, `models.get_api_key`.
- Keep request/response, tool, or helper semantics documented here at the same time as source changes.

## Work Guidance

- Preserve public helper APIs used by core code and plugins unless every caller is updated.
- Keep path, auth, secret, persistence, network, and subprocess behavior explicit and bounded.
- Prefer adding cohesive helper functions here only when behavior is reused across modules.

## Verification

- Run targeted tests for changed helper behavior; run security regressions for auth, filesystem, WebSocket, tunnel, upload, or secret-handling helpers.
- No direct test reference was found by name search; choose the nearest behavioral test or perform a focused smoke check.

## Child DOX Index

No child DOX files.
