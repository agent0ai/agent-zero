# llm_result.py DOX

## Purpose

- Own canonical LLM result metadata shared by model transports, history, and tool-result processing.
- Preserve Responses API output items, provider response IDs, reasoning text, usage, and capability metadata in a serializable form.

## Ownership

- `llm_result.py` owns the runtime implementation.
- `llm_result.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `ResponseItem`
- `ResponseFunctionCall`
- `LLMResult`
- Top-level functions include metadata conversion, function-call output item construction, object normalization, output-text extraction, reasoning extraction, and function-call argument parsing.

## Runtime Contracts

- `LLMResult.metadata()` stores only durable provider state under `RESPONSE_METADATA_KEY`: response IDs, structured output items, provider/mode/state, usage, and capability data. Runtime prompt inputs, raw responses, and duplicated response/reasoning text are not persisted in history.
- `from_response(...)` must preserve provider `response_id`, `previous_response_id`, raw output items, usage, and capability metadata.
- `from_chat(...)` must produce an equivalent chat-completions result with `mode="chat_completions"` and `state="off"`, preserving optional function-call output items when the chat transport supplies them.
- Function-call output items must preserve `call_id` and optional acknowledged safety checks.
- Argument parsing must tolerate JSON strings, dictionaries, and malformed values without throwing.

## Work Guidance

- Keep metadata backward-compatible with existing serialized chat history.
- Treat unknown response item types as preserved built-in items unless they are local function calls, message text, or reasoning.
- Avoid provider-specific assumptions in result parsing.

## Verification

- Run `pytest tests/test_responses_architecture.py -q` after changing result metadata behavior.
- Run focused history/tool-processing tests when changing function-call serialization.

## Child DOX Index

No child DOX files.
