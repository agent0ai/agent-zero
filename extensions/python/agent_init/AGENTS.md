# Agent Init Extensions DOX

## Purpose

- Own backend extensions that run when an agent context initializes.

## Ownership

- Ordered Python files own initial UI message setup and profile settings load behavior.

## Local Contracts

- Keep initialization idempotent for contexts that may be restored or reloaded.
- Preserve ordering between initial message creation and profile settings loading.
- Keep a placeholder user turn (`fw.initial_user_message.md`) ahead of the AI greeting (`fw.initial_message.md`) so `output_langchain` never pops the greeting as a leading `AIMessage`; do not remove either prompt without replacing the turn-order guarantee.
- Minify the initial AI message JSON before storage; preserve raw text as the displayed greeting when JSON parsing fails.
- `_10_initial_message.py` passes `LLMResult.non_llm()` to `hist_add_ai_response` so the Responses-API state seam runs uniformly; the sentinel carries no `response_id` and marks `mode=""`/`state="off"` so stored metadata does not claim a Responses-API turn.
- The synthetic `Hello!` user turn and the AI greeting are intentionally hidden: they have no matching UI log item (branching links log↔history by ID, but these seeding turns predate the log). They serve as a few-shot example of the expected user→AI turn ordering so `output_langchain` does not pop the greeting as a leading `AIMessage`. Do not add log items for seeding turns without replacing the few-shot guarantee.

## Work Guidance

- Coordinate changes with profile loading, settings resolution, and startup smoke checks.

## Verification

- Smoke-test new chat/context initialization after changes.

## Child DOX Index

No child DOX files.
