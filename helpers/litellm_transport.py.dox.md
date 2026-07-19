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
- Do not send orphan tool controls when no tools are present; strict OpenAI-compatible servers can reject empty `tools` arrays.
- Normalize function tool parameter schemas with an explicit object `properties` field before Responses requests so OpenAI-compatible chat backends reached through LiteLLM can validate them.
- Prefer Responses API when configured, but fallback to Chat Completions when the provider does not support Responses.
- Fall back to Chat Completions when a Responses request is rejected before any output by an endpoint-specific or shape-specific Bad Request indicating the provider cannot parse Responses payloads.
- Fall back to Chat Completions when a Responses endpoint fails before output with an endpoint-specific server error, proxy path-unavailable error, or LiteLLM proxy-extra import error.
- Fall back to Chat Completions when LiteLLM's Responses mock streaming path tries to JSON-decode a real SSE stream before any output.
- Preserve Chat Completions tool calls from both non-streaming responses and streaming deltas as canonical `LLMResult` function-call items.
- Preserve provider-state metadata when Responses API calls succeed, and fall back to local replay when provider state is unsupported.
- Keep prompt-cache markers only for providers that accept them.

## Work Guidance

- Add provider-agnostic request cleanup here when multiple OpenAI-compatible providers can benefit.
- Treat fallback behavior as a shared transport contract, not a provider registry.
- Keep tool conversion symmetric between Chat Completions and Responses requests.

## Verification

- Run `pytest tests/test_stream_tool_early_stop.py tests/test_responses_architecture.py -q` after changing transport normalization or fallback behavior.
- Run local-provider smoke checks when changing OpenAI-compatible request cleanup.

## Child DOX Index

No child DOX files.
