# A2A Chat Plugin DOX

## Purpose

- Own the on-demand A2A Chat skill for agent-to-agent communication over FastA2A.

## Ownership

- `skills/a2a-chat/SKILL.md` declares the callable. `extensions/python/skill_tools/` binds it to `helpers/chat_handler.py`, which owns session caching, message extraction, and remote dispatch.
- The tool logs its message as type `a2a_chat` with an `icon://hub Chatting: <agent_url>` headline; `extensions/webui/get_message_handler/` owns the `A2A` badge presentation and `extensions/webui/get_process_step_types/` registers the type.
- `helpers/fasta2a_client.py` owns the FastA2A client connection, message dispatch, and task polling.
- `prompts/` owns the framework messages for failures.
- `plugin.yaml` and `README.md` own metadata and docs.
- `webui/thumbnail.jpg` owns the 256×256 plugin catalog artwork, kept below 20 KB.

## Local Contracts

- Session state is stored on `agent.data["_a2a_sessions"]`, keyed by a normalized agent URL that strips an explicit `/a2a` suffix.
- The callable is available after the chat loads `a2a-chat`. Tool Access retains `plugin:_a2a_chat:a2a_chat` and the existing `local:a2a_chat` alias for both allows and denials.
- The `reset` argument coerces through the shared `coerce_bool` helper instead of returning a repairable error; absent and unrecognized values default to `false`, while numbers retain their truthiness.
- Remote text extraction prefers the newest assistant history message, then status message, then artifacts; an empty extraction returns a distinct failed-response error instead of success.
- The tool reports a2a unavailability without raising.

## Work Guidance

- Keep tool output concise, model-readable, and safe for history persistence.
- Coordinate argument or behavior changes with the tool prompt and the fasta2a client contract.
- Respect intervention flow before remote dispatch and polling.

## Verification

- `tests/test_a2a_chat_tool.py` covers skill loading, Tool Access, and remote conversation reuse through the server's auth/router. Verify that two calls in one live chat send the same remote context ID on follow-up.

## Child DOX Index

No child DOX files.
