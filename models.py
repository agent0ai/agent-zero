from dataclasses import dataclass, field
from enum import Enum
import logging
import os
from typing import (
    Any,
    Awaitable,
    Callable,
    List,
    Optional,
    Iterator,
    AsyncIterator,
    Tuple,
    TypedDict,
)

from litellm import embedding
import litellm
import openai

from helpers import dotenv
from helpers import settings, images
from helpers.dotenv import load_dotenv
from helpers.providers import ModelType as ProviderModelType, get_provider_config
from helpers.rate_limiter import RateLimiter
from helpers.tokens import approximate_tokens
from helpers.extension import extensible  # extensible: allows plugins to intercept get_api_key()
from helpers.litellm_transport import LiteLLMTransport, ResponsesTransport
from helpers.llm_result import LLMResult

from langchain_core.language_models.chat_models import SimpleChatModel
from langchain_core.outputs.chat_generation import ChatGenerationChunk
from langchain_core.callbacks.manager import (
    CallbackManagerForLLMRun,
    AsyncCallbackManagerForLLMRun,
)
from langchain_core.messages import (
    BaseMessage,
    AIMessageChunk,
    HumanMessage,
    SystemMessage,
)
from langchain.embeddings.base import Embeddings
from sentence_transformers import SentenceTransformer
from pydantic import ConfigDict


DEFAULT_LITELLM_GLOBAL_KWARGS: dict[str, Any] = {
    "drop_params": True,
}

# LiteLLM documents drop_params as both a module-level switch and per-call kwarg.
# Other entries in litellm_global_kwargs, such as timeout or additional_drop_params,
# are kept as per-call kwargs instead of becoming arbitrary module attributes.
LITELLM_MODULE_GLOBAL_KEYS = frozenset({"drop_params"})


def _normalize_litellm_kwargs(values: dict[str, Any]) -> dict[str, Any]:
    # Normalize .env/UI-style scalar strings into native types for LiteLLM.
    result: dict[str, Any] = {}
    for k, v in values.items():
        if isinstance(v, str):
            stripped = v.strip()
            lowered = stripped.lower()
            if lowered == "true":
                result[k] = True
            elif lowered == "false":
                result[k] = False
            elif lowered in ("none", "null"):
                result[k] = None
            else:
                try:
                    result[k] = int(stripped)
                except ValueError:
                    try:
                        result[k] = float(stripped)
                    except ValueError:
                        result[k] = v
        else:
            result[k] = v
    return result


def get_litellm_global_kwargs() -> dict[str, Any]:
    kwargs = _normalize_litellm_kwargs(DEFAULT_LITELLM_GLOBAL_KWARGS)
    try:
        configured = settings.get_settings().get("litellm_global_kwargs", {})  # type: ignore[union-attr]
    except Exception:
        configured = {}
    if isinstance(configured, dict):
        kwargs.update(_normalize_litellm_kwargs(configured))
    return kwargs


# keep provider logging quiet in normal operation
def turn_off_logging():
    os.environ["LITELLM_LOG"] = "ERROR"  # only errors
    litellm.suppress_debug_info = True
    # Silence **all** LiteLLM sub-loggers (utils, cost_calculator…)
    for name in logging.Logger.manager.loggerDict:
        if name.lower().startswith("litellm"):
            logging.getLogger(name).setLevel(logging.ERROR)


def set_litellm_params():
    global_kwargs = get_litellm_global_kwargs()
    for key, value in global_kwargs.items():
        if key not in LITELLM_MODULE_GLOBAL_KEYS:
            continue
        setattr(litellm, key, value)
    return global_kwargs


def configure_litellm():
    turn_off_logging()
    set_litellm_params()


def _merge_litellm_call_kwargs(*overrides: dict[str, Any] | None) -> dict[str, Any]:
    kwargs = get_litellm_global_kwargs()
    for override in overrides:
        if isinstance(override, dict):
            kwargs.update(override)
    return kwargs


# init
load_dotenv()
configure_litellm()


class ModelType(Enum):
    CHAT = "Chat"
    EMBEDDING = "Embedding"


@dataclass
class ModelConfig:
    type: ModelType
    provider: str
    name: str
    api_key: str = ""
    api_base: str = ""
    ctx_length: int = 0
    limit_requests: int = 0
    limit_input: int = 0
    limit_output: int = 0
    vision: bool = False
    kwargs: dict = field(default_factory=dict)

    def build_kwargs(self):
        kwargs = self.kwargs.copy() or {}
        if self.api_key and "api_key" not in kwargs:
            kwargs["api_key"] = self.api_key
        if self.api_base and "api_base" not in kwargs:
            kwargs["api_base"] = self.api_base
        return kwargs


class ChatChunk(TypedDict):
    """Simplified response chunk for chat models."""
    response_delta: str
    reasoning_delta: str


class ChatGenerationResult:
    """Chat generation result object"""
    def __init__(self, chunk: ChatChunk|None = None):
        self.reasoning = ""
        self.response = ""
        self.thinking = False
        self.thinking_tag = ""
        self.unprocessed = ""
        self.native_reasoning = False
        self.thinking_pairs = [("<think>", "</think>"), ("<reasoning>", "</reasoning>")]
        if chunk:
            self.add_chunk(chunk)

    def add_chunk(self, chunk: ChatChunk) -> ChatChunk:
        if chunk["reasoning_delta"]:
            self.native_reasoning = True

        # if native reasoning detection works, there's no need to worry about thinking tags
        if self.native_reasoning:
            processed_chunk = ChatChunk(response_delta=chunk["response_delta"], reasoning_delta=chunk["reasoning_delta"])
        else:
            # if the model outputs thinking tags, we ned to parse them manually as reasoning
            processed_chunk = self._process_thinking_chunk(chunk)

        self.reasoning += processed_chunk.get("reasoning_delta", "")
        self.response += processed_chunk.get("response_delta", "")

        return processed_chunk

    def _process_thinking_chunk(self, chunk: ChatChunk) -> ChatChunk:
        response_delta = self.unprocessed + chunk["response_delta"]
        self.unprocessed = ""
        return self._process_thinking_tags(response_delta, chunk["reasoning_delta"])

    def _process_thinking_tags(self, response: str, reasoning: str) -> ChatChunk:
        if self.thinking:
            close_pos = response.find(self.thinking_tag)
            if close_pos != -1:
                reasoning += response[:close_pos]
                response = response[close_pos + len(self.thinking_tag):]
                self.thinking = False
                self.thinking_tag = ""
            else:
                if self._is_partial_closing_tag(response):
                    self.unprocessed = response
                    response = ""
                else:
                    reasoning += response
                    response = ""
        else:
            for opening_tag, closing_tag in self.thinking_pairs:
                if response.startswith(opening_tag):
                    response = response[len(opening_tag):]
                    self.thinking = True
                    self.thinking_tag = closing_tag

                    close_pos = response.find(closing_tag)
                    if close_pos != -1:
                        reasoning += response[:close_pos]
                        response = response[close_pos + len(closing_tag):]
                        self.thinking = False
                        self.thinking_tag = ""
                    else:
                        if self._is_partial_closing_tag(response):
                            self.unprocessed = response
                            response = ""
                        else:
                            reasoning += response
                            response = ""
                    break
                elif len(response) < len(opening_tag) and self._is_partial_opening_tag(response, opening_tag):
                    self.unprocessed = response
                    response = ""
                    break

        return ChatChunk(response_delta=response, reasoning_delta=reasoning)

    def _is_partial_opening_tag(self, text: str, opening_tag: str) -> bool:
        for i in range(1, len(opening_tag)):
            if text == opening_tag[:i]:
                return True
        return False

    def _is_partial_closing_tag(self, text: str) -> bool:
        if not self.thinking_tag or not text:
            return False
        max_check = min(len(text), len(self.thinking_tag) - 1)
        for i in range(1, max_check + 1):
            if text.endswith(self.thinking_tag[:i]):
                return True
        return False

    def output(self) -> ChatChunk:
        response = self.response
        reasoning = self.reasoning
        if self.unprocessed:
            if reasoning and not response:
                reasoning += self.unprocessed
            else:
                response += self.unprocessed
        return ChatChunk(response_delta=response, reasoning_delta=reasoning)


rate_limiters: dict[str, RateLimiter] = {}
api_keys_round_robin: dict[str, int] = {}


@extensible
def get_api_key(service: str) -> str:
    # get api key for the service
    key = (
        dotenv.get_dotenv_value(f"API_KEY_{service.upper()}")
        or dotenv.get_dotenv_value(f"{service.upper()}_API_KEY")
        or dotenv.get_dotenv_value(f"{service.upper()}_API_TOKEN")
        or "None"
    )
    # if the key contains a comma, use round-robin
    if "," in key:
        api_keys = [k.strip() for k in key.split(",") if k.strip()]
        api_keys_round_robin[service] = api_keys_round_robin.get(service, -1) + 1
        key = api_keys[api_keys_round_robin[service] % len(api_keys)]
    return key


def get_rate_limiter(
    provider: str, name: str, requests: int, input: int, output: int
) -> RateLimiter:
    key = f"{provider}\\{name}"
    rate_limiters[key] = limiter = rate_limiters.get(key, RateLimiter(seconds=60))
    limiter.limits["requests"] = requests or 0
    limiter.limits["input"] = input or 0
    limiter.limits["output"] = output or 0
    return limiter


def _is_transient_litellm_error(exc: Exception) -> bool:
    """Uses status_code when available, else falls back to exception types"""
    exc_text = str(getattr(exc, "message", "") or exc).lower()
    status_code = getattr(exc, "status_code", None)
    if isinstance(status_code, int):
        if status_code in (408, 429, 500, 502, 503, 504):
            return True
        # Treat other 5xx as retriable
        if status_code >= 500:
            return True
        # A body-parse failure ("unable to get json response") with a
        # non-2xx status (e.g. a 400 whose body is an HTML proxy/WAF error
        # page) is a permanent request error, not a dropped connection.
        if not 200 <= status_code < 300:
            return False
        # 2xx: the provider closed the connection mid-body; LiteLLM then
        # reports the truncated response with the *original* success status,
        # which is transient even though the HTTP status says success.
        return "unable to get json response" in exc_text

    if "unable to get json response" in exc_text:
        return True

    # Fallback to exception classes mapped by LiteLLM/OpenAI
    transient_types = (
        getattr(openai, "APITimeoutError", Exception),
        getattr(openai, "APIConnectionError", Exception),
        getattr(openai, "RateLimitError", Exception),
        getattr(openai, "APIError", Exception),
        getattr(openai, "InternalServerError", Exception),
        # Some providers map overloads to ServiceUnavailable-like errors
        getattr(openai, "APIStatusError", Exception),
    )
    return isinstance(exc, transient_types)


def _is_direct_deepseek_model(transport: Any) -> bool:
    """True only for the direct DeepSeek API (litellm `deepseek/...` models).

    Third-party hosts serving deepseek-* weights (openrouter/deepseek/...,
    ollama/deepseek-r1, ...) have different streaming/empty-completion
    behavior and must not pay the duplicate-generation retries.
    """
    model = str(getattr(transport, "model", "")).lower()
    return model.startswith("deepseek/")


def _should_retry_truncated_stream(
    transport: Any, *, stream: bool, stopped_early: bool
) -> bool:
    """Detect provider-dropped chat-completions streams.

    DeepSeek intermittently closes streaming connections mid-response; the
    HTTP layer then ends the iterator without an error, so the completion
    never delivers a terminal finish_reason. Partial output from such a
    stream (typically unterminated JSON) must be retried, not parsed.

    Exempted: non-stream calls, the agent's own early-stop (which breaks the
    stream before finish_reason arrives by design), the responses API, and
    third-party-hosted deepseek-* models that may legitimately omit
    finish_reason.
    """
    if not stream or stopped_early:
        return False
    policy = getattr(transport, "policy", None)
    if policy is None or getattr(policy, "using_responses", False):
        return False
    if not _is_direct_deepseek_model(transport):
        return False
    return not getattr(transport, "last_finish_reason", "")


def _should_retry_empty_completion(
    transport: Any, response: str, *, stopped_early: bool
) -> bool:
    """Detect provider-completed but empty completions.

    DeepSeek V4 Flash in thinking/JSON mode occasionally finishes normally
    (finish_reason=stop) with whitespace-only content after a full reasoning
    stream. An empty response can never satisfy the tool protocol, so the
    turn is retried instead of being reported as a misformat.
    """
    if stopped_early:
        return False
    policy = getattr(transport, "policy", None)
    if policy is None or getattr(policy, "using_responses", False):
        return False
    if not _is_direct_deepseek_model(transport):
        return False
    return not response.strip()


async def apply_rate_limiter(
    model_config: ModelConfig | None,
    input_text: str,
    rate_limiter_callback: (
        Callable[[str, str, int, int], Awaitable[bool]] | None
    ) = None,
):
    if not model_config:
        return
    limiter = get_rate_limiter(
        model_config.provider,
        model_config.name,
        model_config.limit_requests,
        model_config.limit_input,
        model_config.limit_output,
    )
    limiter.add(input=approximate_tokens(input_text))
    limiter.add(requests=1)
    await limiter.wait(rate_limiter_callback)
    return limiter


def apply_rate_limiter_sync(
    model_config: ModelConfig | None,
    input_text: str,
    rate_limiter_callback: (
        Callable[[str, str, int, int], Awaitable[bool]] | None
    ) = None,
):
    if not model_config:
        return
    import asyncio, nest_asyncio

    nest_asyncio.apply()
    return asyncio.run(
        apply_rate_limiter(model_config, input_text, rate_limiter_callback)
    )


class LiteLLMChatWrapper(SimpleChatModel):
    model_name: str
    provider: str
    kwargs: dict = {}

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        extra="allow",
        validate_assignment=False,
    )

    def __init__(
        self,
        model: str,
        provider: str,
        model_config: Optional[ModelConfig] = None,
        **kwargs: Any,
    ):
        model_value = f"{provider}/{model}"
        super().__init__(model_name=model_value, provider=provider, kwargs=kwargs)  # type: ignore
        # Set A0 model config as instance attribute after parent init
        self.a0_model_conf = model_config

    @property
    def _llm_type(self) -> str:
        return "litellm-chat"

    def _convert_messages(self, messages: List[BaseMessage], explicit_caching: bool = False) -> List[dict]:
        result = []
        # Map LangChain message types to LiteLLM roles
        role_mapping = {
            "human": "user",
            "ai": "assistant",
            "system": "system",
            "tool": "tool",
        }
        for m in messages:
            role = role_mapping.get(m.type, m.type)
            message_dict = {"role": role, "content": images.prepare_content(m.content)}

            # Handle tool calls for AI messages
            tool_calls = getattr(m, "tool_calls", None)
            if tool_calls:
                # Convert LangChain tool calls to LiteLLM format
                new_tool_calls = []
                for tool_call in tool_calls:
                    # Ensure arguments is a JSON string
                    args = tool_call["args"]
                    if isinstance(args, dict):
                        import json

                        args_str = json.dumps(args)
                    else:
                        args_str = str(args)

                    new_tool_calls.append(
                        {
                            "id": tool_call.get("id", ""),
                            "type": "function",
                            "function": {
                                "name": tool_call["name"],
                                "arguments": args_str,
                            },
                        }
                    )
                message_dict["tool_calls"] = new_tool_calls

            # Handle tool call ID for ToolMessage
            tool_call_id = getattr(m, "tool_call_id", None)
            if tool_call_id:
                message_dict["tool_call_id"] = tool_call_id

            # fix messages with empty content, this breaks some LLMs
            content = message_dict.get("content")
            has_content = bool(content) if not isinstance(content, list) else len(content) > 0
            if not has_content:
                message_dict["content"] = "empty"

            result.append(message_dict)

        return result

    def _call(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        configure_litellm()
        msgs = self._convert_messages(messages)

        # Apply rate limiting if configured
        apply_rate_limiter_sync(self.a0_model_conf, str(msgs))

        call_kwargs = _merge_litellm_call_kwargs(self.kwargs, kwargs)
        transport = LiteLLMTransport(
            model=self.model_name,
            messages=msgs,
            kwargs=call_kwargs,
            stop=stop,
        )
        parsed = transport.complete()
        output = ChatGenerationResult(parsed).output()
        return output["response_delta"]

    def _stream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> Iterator[ChatGenerationChunk]:
        configure_litellm()
        msgs = self._convert_messages(messages)

        # Apply rate limiting if configured
        apply_rate_limiter_sync(self.a0_model_conf, str(msgs))

        result = ChatGenerationResult()
        call_kwargs = _merge_litellm_call_kwargs(self.kwargs, kwargs)
        transport = LiteLLMTransport(
            model=self.model_name,
            messages=msgs,
            kwargs=call_kwargs,
            stop=stop,
        )
        for parsed in transport.stream():
            output = result.add_chunk(parsed)
            if output["response_delta"]:
                yield ChatGenerationChunk(
                    message=AIMessageChunk(content=output["response_delta"])
                )

    async def _astream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[AsyncCallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> AsyncIterator[ChatGenerationChunk]:
        configure_litellm()
        msgs = self._convert_messages(messages)

        # Apply rate limiting if configured
        await apply_rate_limiter(self.a0_model_conf, str(msgs))

        result = ChatGenerationResult()
        call_kwargs = _merge_litellm_call_kwargs(self.kwargs, kwargs)
        transport = LiteLLMTransport(
            model=self.model_name,
            messages=msgs,
            kwargs=call_kwargs,
            stop=stop,
        )
        async for parsed in transport.astream():
            output = result.add_chunk(parsed)
            if output["response_delta"]:
                yield ChatGenerationChunk(
                    message=AIMessageChunk(content=output["response_delta"])
                )

    @extensible
    async def unified_call(
        self,
        system_message="",
        user_message="",
        messages: List[BaseMessage] | None = None,
        response_callback: Callable[[str, str], Awaitable[str | None]] | None = None,
        reasoning_callback: Callable[[str, str], Awaitable[None]] | None = None,
        tokens_callback: Callable[[str, int], Awaitable[None]] | None = None,
        rate_limiter_callback: (
            Callable[[str, str, int, int], Awaitable[bool]] | None
        ) = None,
        explicit_caching: bool = False,
        **kwargs: Any,
    ) -> Tuple[str, str]:

        configure_litellm()

        if not messages:
            messages = []
        # construct messages
        if system_message:
            messages.insert(0, SystemMessage(content=system_message))
        if user_message:
            messages.append(HumanMessage(content=user_message))

        # convert to litellm format
        msgs_conv = self._convert_messages(messages, explicit_caching=explicit_caching)

        # Apply rate limiting if configured
        limiter = await apply_rate_limiter(
            self.a0_model_conf, str(msgs_conv), rate_limiter_callback
        )

        # Prepare call kwargs and retry config (strip A0-only params before calling LiteLLM)
        call_kwargs: dict[str, Any] = _merge_litellm_call_kwargs(
            self.kwargs, kwargs
        )
        if explicit_caching:
            call_kwargs["a0_explicit_prompt_caching"] = True
        max_retries: int = int(call_kwargs.pop("a0_retry_attempts", 2))
        retry_delay_s: float = float(call_kwargs.pop("a0_retry_delay_seconds", 1.5))
        stream = reasoning_callback is not None or response_callback is not None or tokens_callback is not None
        transport = LiteLLMTransport(
            model=self.model_name,
            messages=msgs_conv,
            kwargs=call_kwargs,
        )

        # results
        result = ChatGenerationResult()

        attempt = 0
        while True:
            got_any_chunk = False
            stop_response: str | None = None
            try:
                if stream:
                    async for parsed in transport.astream():
                        got_any_chunk = True
                        output = result.add_chunk(parsed)

                        # collect reasoning delta and call callbacks
                        if output["reasoning_delta"]:
                            if reasoning_callback:
                                await reasoning_callback(output["reasoning_delta"], result.reasoning)
                            if tokens_callback:
                                await tokens_callback(
                                    output["reasoning_delta"],
                                    approximate_tokens(output["reasoning_delta"]),
                                )
                            # Add output tokens to rate limiter if configured
                            if limiter:
                                limiter.add(output=approximate_tokens(output["reasoning_delta"]))
                        # collect response delta and call callbacks
                        if output["response_delta"]:
                            if response_callback:
                                stop_response = await response_callback(
                                    output["response_delta"], result.response
                                )
                            if tokens_callback:
                                await tokens_callback(
                                    output["response_delta"],
                                    approximate_tokens(output["response_delta"]),
                                )
                            # Add output tokens to rate limiter if configured
                            if limiter:
                                limiter.add(output=approximate_tokens(output["response_delta"]))
                        if stop_response is not None:
                            result.response = stop_response
                            break

                # non-stream response
                else:
                    parsed = await transport.acomplete()
                    output = result.add_chunk(parsed)
                    if limiter:
                        if output["response_delta"]:
                            limiter.add(output=approximate_tokens(output["response_delta"]))
                        if output["reasoning_delta"]:
                            limiter.add(output=approximate_tokens(output["reasoning_delta"]))

                # provider dropped the stream mid-response or completed with
                # empty content: discard the partial output and retry the
                # whole turn instead of parsing broken/empty JSON
                truncated = _should_retry_truncated_stream(
                    transport, stream=stream, stopped_early=stop_response is not None
                )
                empty = _should_retry_empty_completion(
                    transport, result.response, stopped_early=stop_response is not None
                )
                if (truncated or empty) and attempt < max_retries:
                    import asyncio

                    attempt += 1
                    result = ChatGenerationResult()
                    await asyncio.sleep(retry_delay_s)
                    continue

                # Successful completion of stream
                return result.response, result.reasoning

            except Exception as e:
                import asyncio

                # Retry only if no chunks received and error is transient
                if got_any_chunk or not _is_transient_litellm_error(e) or attempt >= max_retries:
                    raise
                attempt += 1
                await asyncio.sleep(retry_delay_s)

    @extensible
    async def unified_turn(
        self,
        system_message="",
        user_message="",
        messages: List[BaseMessage] | None = None,
        response_callback: Callable[[str, str], Awaitable[str | None]] | None = None,
        reasoning_callback: Callable[[str, str], Awaitable[None]] | None = None,
        tokens_callback: Callable[[str, int], Awaitable[None]] | None = None,
        rate_limiter_callback: (
            Callable[[str, str, int, int], Awaitable[bool]] | None
        ) = None,
        explicit_caching: bool = False,
        **kwargs: Any,
    ) -> LLMResult:
        """Canonical internal LLM turn with Responses metadata.

        Public plugin-facing callers should keep using ``unified_call``. Core
        orchestration uses this method when it needs response ids, native output
        items, and state/capability metadata.
        """

        configure_litellm()

        if not messages:
            messages = []
        if system_message:
            messages.insert(0, SystemMessage(content=system_message))
        if user_message:
            messages.append(HumanMessage(content=user_message))

        msgs_conv = self._convert_messages(messages, explicit_caching=explicit_caching)

        limiter = await apply_rate_limiter(
            self.a0_model_conf, str(msgs_conv), rate_limiter_callback
        )

        call_kwargs: dict[str, Any] = _merge_litellm_call_kwargs(
            self.kwargs, kwargs
        )
        if explicit_caching:
            call_kwargs["a0_explicit_prompt_caching"] = True
        max_retries: int = int(call_kwargs.pop("a0_retry_attempts", 2))
        retry_delay_s: float = float(call_kwargs.pop("a0_retry_delay_seconds", 1.5))
        stream = (
            reasoning_callback is not None
            or response_callback is not None
            or tokens_callback is not None
        )
        transport = LiteLLMTransport(
            model=self.model_name,
            messages=msgs_conv,
            kwargs=call_kwargs,
        )

        result = ChatGenerationResult()

        attempt = 0
        while True:
            got_any_chunk = False
            stop_response: str | None = None
            try:
                if stream:
                    async for parsed in transport.astream():
                        got_any_chunk = True
                        output = result.add_chunk(parsed)

                        if output["reasoning_delta"]:
                            if reasoning_callback:
                                await reasoning_callback(
                                    output["reasoning_delta"], result.reasoning
                                )
                            if tokens_callback:
                                await tokens_callback(
                                    output["reasoning_delta"],
                                    approximate_tokens(output["reasoning_delta"]),
                                )
                            if limiter:
                                limiter.add(
                                    output=approximate_tokens(
                                        output["reasoning_delta"]
                                    )
                                )

                        if output["response_delta"]:
                            if response_callback:
                                stop_response = await response_callback(
                                    output["response_delta"], result.response
                                )
                            if tokens_callback:
                                await tokens_callback(
                                    output["response_delta"],
                                    approximate_tokens(output["response_delta"]),
                                )
                            if limiter:
                                limiter.add(
                                    output=approximate_tokens(
                                        output["response_delta"]
                                    )
                                )
                            if (
                                stop_response is not None
                                and not transport.policy.using_responses
                            ):
                                result.response = stop_response
                                break
                else:
                    parsed = await transport.acomplete()
                    output = result.add_chunk(parsed)
                    if limiter:
                        if output["response_delta"]:
                            limiter.add(
                                output=approximate_tokens(output["response_delta"])
                            )
                        if output["reasoning_delta"]:
                            limiter.add(
                                output=approximate_tokens(output["reasoning_delta"])
                            )

                # provider dropped the stream mid-response or completed with
                # empty content: discard the partial output and retry the
                # whole turn instead of parsing broken/empty JSON
                truncated = _should_retry_truncated_stream(
                    transport, stream=stream, stopped_early=stop_response is not None
                )
                empty = _should_retry_empty_completion(
                    transport, result.response, stopped_early=stop_response is not None
                )
                if (truncated or empty) and attempt < max_retries:
                    import asyncio

                    attempt += 1
                    result = ChatGenerationResult()
                    await asyncio.sleep(retry_delay_s)
                    continue

                llm_result = transport.last_result or LLMResult.from_chat(
                    response=result.output()["response_delta"],
                    reasoning=result.output()["reasoning_delta"],
                    input_items=ResponsesTransport.input_from_messages(msgs_conv),
                    provider_model_key=self.model_name,
                    capability=transport._capability_metadata(),
                    finish_reason=transport.last_finish_reason,
                )
                if result.output()["response_delta"] and not llm_result.function_calls:
                    llm_result.response = result.output()["response_delta"]
                if result.output()["reasoning_delta"]:
                    llm_result.reasoning = result.output()["reasoning_delta"]
                return llm_result

            except Exception as e:
                import asyncio

                if (
                    got_any_chunk
                    or not _is_transient_litellm_error(e)
                    or attempt >= max_retries
                ):
                    raise
                attempt += 1
                await asyncio.sleep(retry_delay_s)


class LiteLLMEmbeddingWrapper(Embeddings):
    model_name: str
    kwargs: dict = {}
    a0_model_conf: Optional[ModelConfig] = None

    def __init__(
        self,
        model: str,
        provider: str,
        model_config: Optional[ModelConfig] = None,
        **kwargs: Any,
    ):
        self.model_name = f"{provider}/{model}" if provider != "openai" else model
        self.kwargs = kwargs
        self.a0_model_conf = model_config

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        configure_litellm()
        # Apply rate limiting if configured
        apply_rate_limiter_sync(self.a0_model_conf, " ".join(texts))

        resp = embedding(
            model=self.model_name,
            input=texts,
            **_merge_litellm_call_kwargs(self.kwargs),
        )
        return [
            item.get("embedding") if isinstance(item, dict) else item.embedding  # type: ignore
            for item in resp.data  # type: ignore
        ]

    def embed_query(self, text: str) -> List[float]:
        configure_litellm()
        # Apply rate limiting if configured
        apply_rate_limiter_sync(self.a0_model_conf, text)

        resp = embedding(
            model=self.model_name,
            input=[text],
            **_merge_litellm_call_kwargs(self.kwargs),
        )
        item = resp.data[0]  # type: ignore
        return item.get("embedding") if isinstance(item, dict) else item.embedding  # type: ignore


class LocalSentenceTransformerWrapper(Embeddings):
    """Local wrapper for sentence-transformers models to avoid HuggingFace API calls"""

    def __init__(
        self,
        provider: str,
        model: str,
        model_config: Optional[ModelConfig] = None,
        **kwargs: Any,
    ):
        # Clean common user-input mistakes
        model = model.strip().strip('"').strip("'")

        # Remove the "sentence-transformers/" prefix if present
        if model.startswith("sentence-transformers/"):
            model = model[len("sentence-transformers/") :]

        # Filter kwargs for SentenceTransformer only (no LiteLLM params like 'stream_timeout')
        st_allowed_keys = {
            "device",
            "cache_folder",
            "use_auth_token",
            "revision",
            "trust_remote_code",
            "model_kwargs",
        }
        st_kwargs = {k: v for k, v in (kwargs or {}).items() if k in st_allowed_keys}

        self.model = SentenceTransformer(model, **st_kwargs)
        self.model_name = model
        self.a0_model_conf = model_config

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        # Apply rate limiting if configured
        apply_rate_limiter_sync(self.a0_model_conf, " ".join(texts))

        embeddings = self.model.encode(texts, convert_to_tensor=False)  # type: ignore
        return embeddings.tolist() if hasattr(embeddings, "tolist") else embeddings  # type: ignore

    def embed_query(self, text: str) -> List[float]:
        # Apply rate limiting if configured
        apply_rate_limiter_sync(self.a0_model_conf, text)

        embedding = self.model.encode([text], convert_to_tensor=False)  # type: ignore
        result = (
            embedding[0].tolist() if hasattr(embedding[0], "tolist") else embedding[0]
        )
        return result  # type: ignore


def _get_litellm_chat(
    cls: type = LiteLLMChatWrapper,
    model_name: str = "",
    provider_name: str = "",
    model_config: Optional[ModelConfig] = None,
    **kwargs: Any,
):
    # use api key from kwargs or env
    api_key = kwargs.pop("api_key", None) or get_api_key(provider_name)

    # Only pass API key if key is not a placeholder
    if api_key and api_key not in ("None", "NA"):
        kwargs["api_key"] = api_key

    provider_name, model_name, kwargs = _adjust_call_args(
        provider_name, model_name, kwargs
    )
    return cls(
        provider=provider_name, model=model_name, model_config=model_config, **kwargs
    )


def _get_litellm_embedding(
    model_name: str,
    provider_name: str,
    model_config: Optional[ModelConfig] = None,
    **kwargs: Any,
):
    # Check if this is a local sentence-transformers model
    if provider_name == "huggingface" and model_name.startswith(
        "sentence-transformers/"
    ):
        # Use local sentence-transformers instead of LiteLLM for local models
        provider_name, model_name, kwargs = _adjust_call_args(
            provider_name, model_name, kwargs
        )
        return LocalSentenceTransformerWrapper(
            provider=provider_name,
            model=model_name,
            model_config=model_config,
            **kwargs,
        )

    # use api key from kwargs or env
    api_key = kwargs.pop("api_key", None) or get_api_key(provider_name)

    # Only pass API key if key is not a placeholder
    if api_key and api_key not in ("None", "NA"):
        kwargs["api_key"] = api_key

    provider_name, model_name, kwargs = _adjust_call_args(
        provider_name, model_name, kwargs
    )
    return LiteLLMEmbeddingWrapper(
        model=model_name, provider=provider_name, model_config=model_config, **kwargs
    )



def _adjust_call_args(provider_name: str, model_name: str, kwargs: dict):

    # remap other to openai for litellm
    if provider_name == "other":
        provider_name = "openai"

    return provider_name, model_name, kwargs


def _merge_provider_defaults(
    provider_type: ProviderModelType, original_provider: str, kwargs: dict
) -> tuple[str, dict]:
    provider_name = original_provider  # default: unchanged
    cfg = get_provider_config(provider_type, original_provider)
    if cfg:
        provider_name = cfg.get("litellm_provider", original_provider).lower()

        # Extra arguments nested under `kwargs` for readability
        extra_kwargs = cfg.get("kwargs") if isinstance(cfg, dict) else None  # type: ignore[arg-type]
        if isinstance(extra_kwargs, dict):
            for k, v in extra_kwargs.items():
                kwargs.setdefault(k, v)

    # Inject API key based on the *original* provider id if still missing
    if "api_key" not in kwargs:
        key = get_api_key(original_provider)
        if key and key not in ("None", "NA"):
            kwargs["api_key"] = key

    return provider_name, kwargs


def get_chat_model(
    provider: str, name: str, model_config: Optional[ModelConfig] = None, **kwargs: Any
) -> LiteLLMChatWrapper:
    orig = provider.lower()
    provider_name, kwargs = _merge_provider_defaults("chat", orig, kwargs)
    return _get_litellm_chat(
        LiteLLMChatWrapper, name, provider_name, model_config, **kwargs
    )

def get_embedding_model(
    provider: str, name: str, model_config: Optional[ModelConfig] = None, **kwargs: Any
) -> LiteLLMEmbeddingWrapper | LocalSentenceTransformerWrapper:
    orig = provider.lower()
    provider_name, kwargs = _merge_provider_defaults("embedding", orig, kwargs)
    return _get_litellm_embedding(name, provider_name, model_config, **kwargs)
