# Message Loop Prompts After Extensions DOX

## Purpose

- Own prompt protocol, prompt extras, and history reattachment around primary message-loop prompt construction.

## Ownership

- Ordered Python files own current datetime, relevant-skill hints, loaded-skill history reattachment, agent info, parallel job status, and workdir extras injection.
- Explicitly loaded skill bodies belong in tool-result history with metadata so they can survive persistence and be reattached after compaction.
- Explicitly loaded skill IDs are chat-wide context data, not agent-local state.
- Skills must not write selected or loaded skill bodies into protocol or extras.

## Local Contracts

- Keep injected content bounded and clearly attributed.
- Preserve ordering where later prompt extras depend on earlier recall or load results.
- Do not expose secrets or private files from workdir extras.
- Relevant-skill recall should search the raw user message when available, not the rendered history wrapper.

## Work Guidance

- Coordinate prompt protocol, history-reattachment, and prompt-extra changes with skill, workdir, and profile contracts.

## Verification

- Inspect rendered prompt protocol/history/extras or run prompt-construction tests after changes.

## Child DOX Index

No child DOX files.
