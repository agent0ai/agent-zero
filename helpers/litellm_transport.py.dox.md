# litellm_transport.py DOX

## Purpose

- Own Agent Zero's LiteLLM transport adapter for Chat Completions and Responses API calls.
- Normalize Agent Zero model-call kwargs into provider-safe LiteLLM requests.
- Preserve canonical response metadata for history, provider-state continuation, and fallback decisions.

## Ownership

- `litellm_transport.py` owns the runtime implementation.
- `litellm_transport.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `TransportMode`
- `TransportRecovery`
- `TransportPolicy`
- `LiteLLMTransport`
- `ChatCompletionsTransport`
- `ResponsesTransport`
- `ResponsesEventParser`
- Top-level functions include transport cache reset, request normalization, parsing, prompt-cache preparation, and response/error classifiers.

## Runtime Contracts

- Keep provider selection and provider-specific defaults outside this helper; callers pass a resolved LiteLLM model name and kwargs.
- Strip Agent Zero internal kwargs before sending requests to LiteLLM.
- Validate internal `responses_history_context` against selected prepared local input, bind its stable-prefix digest to actual affinity/tool schemas, and project eligible groups through `responses_history`. Strip the control on every provider path and omit its digest from Chat/fallback result metadata.
- Apply `responses_prompt_replacements` only to Responses input when generated A0 functions are present; preserve original Chat/fallback messages and strip this internal control before either provider call.
- Do not send orphan tool controls when no tools are present; strict OpenAI-compatible servers can reject empty `tools` arrays.
- When Agent Zero function tools are present, default Responses requests to one required native call; explicit request-level `tool_choice` and `parallel_tool_calls` values still win.
- Normalize function tool parameter schemas with an explicit object `properties` field before Responses requests so OpenAI-compatible chat backends reached through LiteLLM can validate them.
- Default to Chat Completions; use Responses only when `a0_api_mode` explicitly selects it, with fallback to Chat Completions when unsupported.
- Fall back to Chat Completions when a Responses request is rejected before any output by an endpoint-specific or shape-specific Bad Request indicating the provider cannot parse Responses payloads.
- Treat opaque type-discrimination errors such as `cannot determine type` from OpenAI-compatible Responses endpoints as shape-specific rejections.
- Fall back to Chat Completions when a Responses endpoint fails before output with an endpoint-specific server error, proxy path-unavailable error, or LiteLLM proxy-extra import error.
- Fall back to Chat Completions when LiteLLM's Responses mock streaming path tries to JSON-decode a real SSE stream before any output.
- Preserve Chat Completions tool calls from both non-streaming responses and streaming deltas as canonical `LLMResult` function-call items.
- Preserve provider usage and LiteLLM response cost for both transports only when the response or stream actually supplies them; do not synthesize unavailable provider accounting.
- Recover all Responses output items from stream events when a terminal completed envelope omits them, including encrypted reasoning. Merge by item/call identity in output-index order; terminal non-null fields win without duplicating calls.
- Stream named native function arguments through canonical tool envelopes for display. Buffer interleaved calls until the active envelope closes; preserve independent original call metadata. Native execution still waits for the completed model turn.
- Fail incomplete Responses generations and native-call streams that end without completion; never promote partial call previews to a Chat result.
- Serialize synthesized Responses function-call JSON with literal Unicode so streamed raw-response logs preserve tool arguments.
- Preserve provider-state metadata when Responses API calls succeed, and fall back to local replay when provider state is unsupported.
- Keep prompt-cache markers only for providers that accept them.

## Work Guidance

- Add provider-agnostic request cleanup here when multiple OpenAI-compatible providers can benefit.
- Treat fallback behavior as a shared transport contract, not a provider registry.
- Keep tool conversion symmetric between Chat Completions and Responses requests.

- TransportMode.from_value owns API-mode interpretation; input_from_model_messages owns model-message conversion shared with Agent and replay preparation.

## Verification

- Run `pytest tests/test_stream_tool_early_stop.py tests/test_responses_architecture.py -q` after changing transport normalization or fallback behavior.
- Run local-provider smoke checks when changing OpenAI-compatible request cleanup.

## Child DOX Index

No child DOX files.

## Chat reasoning boundary

- Chat Completions `reasoning_content` is readable text only up to the provider serialization marker `__ENCRYPTED_REASONING__`. Suppress that marker and its remaining opaque payload before callbacks and result metadata, including markers split across stream chunks. Preserve ordinary reasoning and response content.
- Responses encrypted output items remain opaque native state; this Chat filter neither decodes nor promotes them into text. Existing saved logs are not rewritten.
- Verify with `pytest tests/test_chat_encrypted_reasoning.py -q`.
