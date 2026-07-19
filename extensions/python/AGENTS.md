# Python Extensions DOX

## Purpose

- Own built-in backend lifecycle extensions under `extensions/python/`.
- Keep Python hook behavior compatible with `helpers.extension.call_extensions_async` and `call_extensions_sync`.

## Ownership

- Each direct subdirectory is one named extension point.
- Python files inside an extension point are loaded in deterministic filename order.
- Implicit `@extensible` hook implementations use `_functions/<module>/<qualname>/<start|end>/` layout when present.

## Local Contracts

- Extension functions must match the arguments supplied by their hook point.
- Preserve numeric prefixes when ordering affects prompt construction, stream masking, persistence, or cleanup.
- Use `AgentContext` from `agent` when context access is needed.
- Do not log unmasked secrets, raw hidden prompt sections, or private user data.

## Work Guidance

- Keep extension modules import-light; many hooks run during hot paths.
- Use mutable `ctx` or `data` dictionaries according to the hook contract when rewriting content.
- Add or update tests when a hook changes prompt content, message history, tool output, streaming, or persistence behavior.

## Verification

- Run targeted tests for the affected lifecycle area.
- Run a startup smoke check for `agent_init`, `startup_migration`, or `system_prompt` changes when practical.

## Child DOX Index

Direct child DOX files:

| Child | Scope |
| --- | --- |
| [_functions/AGENTS.md](_functions/AGENTS.md) | Implicit `@extensible` backend hook implementations. |
| [agent_init/AGENTS.md](agent_init/AGENTS.md) | Agent context initialization hooks. |
| [banners/AGENTS.md](banners/AGENTS.md) | Backend banner and discovery-card contributions. |
| [before_main_llm_call/AGENTS.md](before_main_llm_call/AGENTS.md) | Pre-main-model-call behavior. |
| [error_format/AGENTS.md](error_format/AGENTS.md) | Error formatting and masking behavior. |
| [hist_add_before/AGENTS.md](hist_add_before/AGENTS.md) | Pre-history-insertion masking behavior. |
| [hist_add_tool_result/AGENTS.md](hist_add_tool_result/AGENTS.md) | Tool-result history side effects. |
| [job_loop/AGENTS.md](job_loop/AGENTS.md) | Periodic backend maintenance jobs. |
| [message_loop_end/AGENTS.md](message_loop_end/AGENTS.md) | End-of-message-loop history and persistence behavior. |
| [message_loop_prompts_after/AGENTS.md](message_loop_prompts_after/AGENTS.md) | Prompt protocol and extras assembled around message-loop prompt construction. |
| [message_loop_prompts_before/AGENTS.md](message_loop_prompts_before/AGENTS.md) | Pre-prompt-construction message-loop gates. |
| [message_loop_start/AGENTS.md](message_loop_start/AGENTS.md) | Start-of-message-loop iteration state. |
| [monologue_end/AGENTS.md](monologue_end/AGENTS.md) | End-of-monologue UI and cleanup behavior. |
| [monologue_start/AGENTS.md](monologue_start/AGENTS.md) | Start-of-monologue behavior such as chat renaming. |
| [process_chain_end/AGENTS.md](process_chain_end/AGENTS.md) | Process-chain completion and queued-message handling. |
| [reasoning_stream/AGENTS.md](reasoning_stream/AGENTS.md) | Full reasoning stream handling. |
| [reasoning_stream_chunk/AGENTS.md](reasoning_stream_chunk/AGENTS.md) | Reasoning stream chunk masking. |
| [reasoning_stream_end/AGENTS.md](reasoning_stream_end/AGENTS.md) | Reasoning stream finalization. |
| [response_stream/AGENTS.md](response_stream/AGENTS.md) | Full assistant response stream handling. |
| [response_stream_chunk/AGENTS.md](response_stream_chunk/AGENTS.md) | Assistant response chunk masking. |
| [response_stream_end/AGENTS.md](response_stream_end/AGENTS.md) | Assistant response stream finalization. |
| [startup_migration/AGENTS.md](startup_migration/AGENTS.md) | Startup migrations. |
| [system_prompt/AGENTS.md](system_prompt/AGENTS.md) | Core system prompt section construction. |
| [tool_execute_after/AGENTS.md](tool_execute_after/AGENTS.md) | Post-tool-execution processing. |
| [tool_execute_before/AGENTS.md](tool_execute_before/AGENTS.md) | Pre-tool-execution processing. |
| [user_message_ui/AGENTS.md](user_message_ui/AGENTS.md) | User-visible UI message hooks. |
| [util_model_call_before/AGENTS.md](util_model_call_before/AGENTS.md) | Pre-utility-model-call masking. |
| [webui_ws_connect/AGENTS.md](webui_ws_connect/AGENTS.md) | WebUI WebSocket connect behavior. |
| [webui_ws_disconnect/AGENTS.md](webui_ws_disconnect/AGENTS.md) | WebUI WebSocket disconnect behavior. |
| [webui_ws_event/AGENTS.md](webui_ws_event/AGENTS.md) | Incoming WebUI WebSocket event behavior. |
