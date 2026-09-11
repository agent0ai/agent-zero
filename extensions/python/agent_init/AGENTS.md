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
- The synthetic `Hello!` user turn has no UI log. The assistant greeting is displayed as a response log with the same ID as its history message, preserving the log/history link for branching. Keep the user-first seed without duplicating the visible greeting on reload.

## Work Guidance

- Coordinate changes with profile loading, settings resolution, and startup smoke checks.

## Verification

- Smoke-test new chat/context initialization after changes.

## Child DOX Index

No child DOX files.
