from dataclasses import dataclass, field
import asyncio
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

from litellm import completion, acompletion, embedding
import litellm

from python.helpers import dotenv
from python.helpers import settings
from python.helpers.dotenv import load_dotenv
from python.helpers.providers import get_provider_config
from python.helpers.rate_limiter import RateLimiter
from python.helpers.tokens import approximate_tokens
from python.helpers import errors

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


# disable extra logging, must be done repeatedly, otherwise browser-use will turn it back on for some reason
def turn_off_logging():
    os.environ["LITELLM_LOG"] = "ERROR"  # only errors
    litellm.suppress_debug_info = True
    # Silence **all** LiteLLM sub-loggers (utils, cost_calculator…)
    for name in logging.Logger.manager.loggerDict:
        if name.lower().startswith("litellm"):
            logging.getLogger(name).setLevel(logging.ERROR)


# init
load_dotenv()
turn_off_logging()
litellm.modify_params = True  # helps fix anthropic tool calls by browser-use


class ModelType(Enum):
    CHAT = "Chat"
    EMBEDDING = "Embedding"


@dataclass
class ModelConfig:
    type: ModelType
    provider: str
    name: str
    api_base: str = ""
    ctx_length: int = 0
    limit_requests: int = 0
    limit_input: int = 0
    limit_output: int = 0
    vision: bool = False
    kwargs: dict = field(default_factory=dict)

    def build_kwargs(self):
        kwargs = self.kwargs.copy() or {}
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
            # if the model outputs thinking tags, we need to parse them manually as reasoning
            processed_chunk = self._process_thinking_chunk(chunk)
        
        self.reasoning += processed_chunk["reasoning_delta"]
        self.response += processed_chunk["response_delta"]
        
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

    class Config:
        arbitrary_types_allowed = True
        extra = "allow"  # Allow extra attributes
        validate_assignment = False  # Don't validate on assignment

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

    def _convert_messages(self, messages: List[BaseMessage]) -> List[dict]:
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
            message_dict = {"role": role, "content": m.content}

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

            result.append(message_dict)
        return result

    def _call(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        import asyncio

        msgs = self._convert_messages(messages)

        # Apply rate limiting if configured
        apply_rate_limiter_sync(self.a0_model_conf, str(msgs))

        # Call the model
        resp = completion(
            model=self.model_name, messages=msgs, stop=stop, **{**self.kwargs, **kwargs}
        )

        # Parse output
        parsed = _parse_chunk(resp)
        output = ChatGenerationResult(parsed).output()
        return output["response_delta"]

    def _stream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> Iterator[ChatGenerationChunk]:
        import asyncio

        msgs = self._convert_messages(messages)

        # Apply rate limiting if configured
        apply_rate_limiter_sync(self.a0_model_conf, str(msgs))

        result = ChatGenerationResult()

        for chunk in completion(
            model=self.model_name,
            messages=msgs,
            stream=True,
            stop=stop,
            **{**self.kwargs, **kwargs},
        ):
            # parse chunk
            parsed = _parse_chunk(chunk) # chunk parsing
            output = result.add_chunk(parsed) # chunk processing

            # Only yield chunks with non-None content
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
        msgs = self._convert_messages(messages)

        # Apply rate limiting if configured
        await apply_rate_limiter(self.a0_model_conf, str(msgs))

        result = ChatGenerationResult()

        response = await acompletion(
            model=self.model_name,
            messages=msgs,
            stream=True,
            stop=stop,
            **{**self.kwargs, **kwargs},
        )
        async for chunk in response:  # type: ignore
            # parse chunk
            parsed = _parse_chunk(chunk) # chunk parsing
            output = result.add_chunk(parsed) # chunk processing

            # Only yield chunks with non-None content
            if output["response_delta"]:
                yield ChatGenerationChunk(
                    message=AIMessageChunk(content=output["response_delta"])
                )

    async def unified_call(
        self,
        system_message="",
        user_message="",
        messages: List[BaseMessage] | None = None,
        response_callback: Callable[[str, str], Awaitable[None]] | None = None,
        reasoning_callback: Callable[[str, str], Awaitable[None]] | None = None,
        tokens_callback: Callable[[str, int], Awaitable[None]] | None = None,
        rate_limiter_callback: (
            Callable[[str, str, int, int], Awaitable[bool]] | None
        ) = None,
        attempt_log_callback: Callable[[dict, str], Awaitable[None]] | None = None,
        **kwargs: Any,
    ) -> Tuple[str, str]:
        """Unified entry (Scheme 1): adaptive timeouts, rate limiting, global retries, API key rotation, and streaming callbacks."""
        turn_off_logging()

        # Build message payload
        if not messages:
            messages = []
        if system_message:
            messages.insert(0, SystemMessage(content=system_message))
        if user_message:
            messages.append(HumanMessage(content=user_message))
        msgs_conv = self._convert_messages(messages)

        usage_kind = getattr(self, "usage_kind", "chat")  # chat | utility
        setts = settings.get_settings()  # type: ignore

        # Adaptive timeout (base + per_1k + optional auto)
        mode = setts.get("adaptive_timeout_mode", "basic")
        adaptive_enabled = mode in ("basic", "auto")
        # defaults from settings schema
        if usage_kind == "utility":
            base_default = float(setts.get("util_timeout_base", 6.0))
            per1k_default = float(setts.get("util_timeout_per_1k", 4.0))
        else:
            base_default = float(setts.get("chat_timeout_base", 8.0))
            per1k_default = float(setts.get("chat_timeout_per_1k", 6.0))

        # Optional overrides from LiteLLM global parameters textbox (four canonical keys only)
        try:
            global_kwargs = setts.get("litellm_global_kwargs", {}) or {}
        except Exception:
            global_kwargs = {}

        def _get_override(keys: list[str], default_val: float) -> float:
            if not isinstance(global_kwargs, dict):
                return default_val
            norm = {str(k).lower(): v for k, v in global_kwargs.items()}
            for k in keys:
                kk = k.lower()
                if kk in norm:
                    try:
                        return float(norm[kk])
                    except Exception:
                        continue
            return default_val

        if usage_kind == "utility":
            # Only accept the new readable keys
            base = _get_override(["util_timeout_base"], base_default) if adaptive_enabled else base_default
            per_1k = _get_override(["util_timeout_per_1k"], per1k_default) if adaptive_enabled else per1k_default
        else:
            base = _get_override(["chat_timeout_base"], base_default) if adaptive_enabled else base_default
            per_1k = _get_override(["chat_timeout_per_1k"], per1k_default) if adaptive_enabled else per1k_default

        prompt_tokens = approximate_tokens(str(msgs_conv))
        est_timeout = base + (prompt_tokens / 1000.0) * per_1k if adaptive_enabled else None
        slow_mult_cfg = float(setts.get("adaptive_slow_multiplier", 10.0))
        cap_cfg = float(setts.get("adaptive_timeout_cap", 0.0))

        # If previously flagged as slow (from stats or prior timeouts) -> scale initial timeout
        timeout_scale = 1.0
        if mode == "auto" and getattr(self, "_slow_model_flag", False) and est_timeout is not None:
            timeout_scale = max(timeout_scale, slow_mult_cfg)

        # Carry over escalation from previous timeouts (_timeout_escalate)
        if mode == "auto" and hasattr(self, "_timeout_escalate"):
            try:
                timeout_scale = max(timeout_scale, float(getattr(self, "_timeout_escalate")))
            except Exception:
                pass

        final_timeout = None
        if est_timeout is not None:
            final_timeout = est_timeout * timeout_scale
            if cap_cfg > 0 and final_timeout > cap_cfg:
                final_timeout = cap_cfg
            # Apply timeout and stream_timeout for the first attempt
            kwargs.setdefault("timeout", final_timeout)
            kwargs.setdefault("stream_timeout", final_timeout)
        if final_timeout is not None:
            # Expose to outer pipeline (e.g., memory consolidation)
            self._last_final_timeout = final_timeout  # type: ignore
        # Save current scale for subsequent retries
        self._timeout_current_scale = timeout_scale  # type: ignore
        if final_timeout is not None:
            self._retry_timeout_override = final_timeout  # type: ignore

        # Auto speed detection (auto mode)
        auto_speed = (mode == "auto") and adaptive_enabled and est_timeout is not None
        if auto_speed:
            if not hasattr(self, "_speed_stats"):
                self._speed_stats = {  # type: ignore
                    "first_token_latency": -1.0,
                    "throughput": -1.0,
                }
            decay = 0.3
            slow_first = 8.0
            slow_tp = 25.0
            slow_mult = slow_mult_cfg
            max_cap = cap_cfg
            start_time = asyncio.get_event_loop().time()
            first_token_time_holder = {"t": -1.0}
            token_counter = {"n": 0}
            orig_response_cb = response_callback
            orig_reasoning_cb = reasoning_callback

            async def prof_response_cb(delta: str, total: str):
                if first_token_time_holder["t"] < 0 and delta:
                    first_token_time_holder["t"] = asyncio.get_event_loop().time() - start_time
                token_counter["n"] += approximate_tokens(delta)
                if orig_response_cb:
                    await orig_response_cb(delta, total)

            async def prof_reasoning_cb(delta: str, total: str):
                if first_token_time_holder["t"] < 0 and delta:
                    first_token_time_holder["t"] = asyncio.get_event_loop().time() - start_time
                token_counter["n"] += approximate_tokens(delta)
                if orig_reasoning_cb:
                    await orig_reasoning_cb(delta, total)

            response_callback = prof_response_cb  # type: ignore
            reasoning_callback = prof_reasoning_cb  # type: ignore

            async def _update_stats():
                try:
                    end_time = asyncio.get_event_loop().time()
                    total_time = end_time - start_time
                    ft = first_token_time_holder["t"] if first_token_time_holder["t"] >= 0 else total_time
                    tp = (token_counter["n"] / max(total_time - (first_token_time_holder["t"] or 0.0), 0.001)) if token_counter["n"] else 0.0
                    ss = self._speed_stats  # type: ignore
                    ss["first_token_latency"] = ft if ss["first_token_latency"] < 0 else (1 - decay) * ss["first_token_latency"] + decay * ft
                    ss["throughput"] = tp if ss["throughput"] < 0 else (1 - decay) * ss["throughput"] + decay * tp
                    is_slow = (ss["first_token_latency"] or 0) > slow_first or (ss["throughput"] or 1e9) < slow_tp
                    if is_slow and est_timeout is not None:
                        scaled = est_timeout * slow_mult  # For next call (current request cannot increase underlying timeout)
                        if max_cap > 0:
                            scaled = min(scaled, max_cap)
                        # Mark slow model; raise baseline for next calls
                        self._slow_model_flag = True  # type: ignore
                        self._timeout_escalate = max(getattr(self, "_timeout_escalate", 1.0), slow_mult)  # type: ignore
                except Exception:
                    pass

            self._after_unified_call_speed_update = _update_stats  # type: ignore
        else:
            self._after_unified_call_speed_update = None  # type: ignore

        # Rate limiter
        limiter = await apply_rate_limiter(self.a0_model_conf, str(msgs_conv), rate_limiter_callback)

        # API key rotation
        service = self.provider
        from python.helpers import dotenv as _dz
        svc_up = service.upper()
        raw_key = (
            _dz.get_dotenv_value(f"API_KEY_{svc_up}")
            or _dz.get_dotenv_value(f"{svc_up}_API_KEY")
            or _dz.get_dotenv_value(f"{svc_up}_API_TOKEN")
        )
        key_list: list[str] = []
        if raw_key:
            if "," in raw_key:
                key_list = [k.strip() for k in raw_key.split(",") if k.strip()]
            else:
                key_list = [raw_key.strip()] if raw_key.strip() else []
        if not hasattr(self, "_key_health"):
            self._key_health = {k: {"fail": 0, "cooldown": 0.0} for k in key_list}

        def _select_key():
            if not key_list:
                return None
            now = asyncio.get_event_loop().time()
            health = self._key_health
            candidates = [k for k in key_list if health.get(k, {}).get("cooldown", 0) <= now]
            if candidates:
                return sorted(candidates, key=lambda k: (health[k]["fail"], health[k]["cooldown"]))[0]
            return sorted(key_list, key=lambda k: health.get(k, {}).get("cooldown", 0))[0]

        def _mark_good(k: str | None):
            if k and k in self._key_health:
                self._key_health[k]["fail"] = 0

        def _mark_bad(k: str | None, info: errors.ErrorInfo):
            if k and k in self._key_health:
                self._key_health[k]["fail"] += 1
                if info.rotate_key:
                    cd = asyncio.get_event_loop().time() + 5 + self._key_health[k]["fail"] * 2
                    self._key_health[k]["cooldown"] = cd

        async def _log(ev: dict):
            try:
                if ev.get("action") == "retry":
                    if ev.get("error_class") == "timeout" and mode == "auto":
                        self._slow_model_flag = True  # type: ignore
                        prev_call_scale = float(getattr(self, "_timeout_current_scale", 1.0))
                        prev_escalate = float(getattr(self, "_timeout_escalate", 1.0))
                        base_scale_target = max(prev_escalate, slow_mult_cfg)
                        new_scale = max(prev_call_scale, base_scale_target)
                        if cap_cfg > 0 and est_timeout:
                            max_allowed_scale = cap_cfg / max(est_timeout, 0.001)
                            if new_scale > max_allowed_scale:
                                new_scale = max_allowed_scale
                        self._timeout_escalate = new_scale
                        self._timeout_current_scale = new_scale
                        if est_timeout and est_timeout > 0:
                            new_timeout = est_timeout * new_scale
                            if cap_cfg > 0 and new_timeout > cap_cfg:
                                new_timeout = cap_cfg
                            self._retry_timeout_override = new_timeout  # type: ignore
                if attempt_log_callback:
                    await attempt_log_callback(ev, usage_kind)
            except Exception:
                pass

        async def _op(api_key: str | None):
            call_kwargs = {**self.kwargs, **kwargs}
            if api_key:
                call_kwargs["api_key"] = api_key
            override = getattr(self, "_retry_timeout_override", None)
            if override:
                call_kwargs["timeout"] = override
                call_kwargs["stream_timeout"] = override
            _completion = await acompletion(
                model=self.model_name,
                messages=msgs_conv,
                stream=True,
                **call_kwargs,
            )
            result = ChatGenerationResult()
            sent_response_len = 0
            sent_reasoning_len = 0
            async for chunk in _completion:  # type: ignore
                parsed = _parse_chunk(chunk)
                output = result.add_chunk(parsed)
                if output["reasoning_delta"]:
                    if reasoning_callback:
                        await reasoning_callback(output["reasoning_delta"], result.reasoning)
                    if tokens_callback:
                        await tokens_callback(output["reasoning_delta"], approximate_tokens(output["reasoning_delta"]))
                    if limiter:
                        limiter.add(output=approximate_tokens(output["reasoning_delta"]))
                    sent_reasoning_len = len(result.reasoning)
                if output["response_delta"]:
                    if response_callback:
                        await response_callback(output["response_delta"], result.response)
                    if tokens_callback:
                        await tokens_callback(output["response_delta"], approximate_tokens(output["response_delta"]))
                    if limiter:
                        limiter.add(output=approximate_tokens(output["response_delta"]))
                    sent_response_len = len(result.response)
            try:
                final_chunk = result.output()
                final_resp = final_chunk["response_delta"]
                final_reas = final_chunk["reasoning_delta"]
                if response_callback and len(final_resp) > sent_response_len:
                    tail = final_resp[sent_response_len:]
                    if tail:
                        await response_callback(tail, final_resp)
                        if tokens_callback:
                            await tokens_callback(tail, approximate_tokens(tail))
                if reasoning_callback and len(final_reas) > sent_reasoning_len:
                    tail_r = final_reas[sent_reasoning_len:]
                    if tail_r:
                        await reasoning_callback(tail_r, final_reas)
                        if tokens_callback:
                            await tokens_callback(tail_r, approximate_tokens(tail_r))
            except Exception:
                pass
            return result.response, result.reasoning

        retry_cfg = errors.RetryConfig(
            max_attempts=int(setts.get("global_retry_max", 3)),
            base_delay=float(setts.get("global_retry_base_delay", 1.0)),
        )
        outcome = await errors.execute_with_retry(
            _op,
            select_key=_select_key if key_list else None,
            mark_key_good=_mark_good if key_list else None,
            mark_key_bad=_mark_bad if key_list else None,
            retry_cfg=retry_cfg,
            log_cb=_log,
        )
        if not outcome.ok:
            raise outcome.final_error or Exception("Model call failed")

        updater = getattr(self, "_after_unified_call_speed_update", None)
        if updater:
            try:
                await updater()
            except Exception:
                pass
        return outcome.result


class BrowserCompatibleChatWrapper(LiteLLMChatWrapper):
    """
    A wrapper for browser agent that can filter/sanitize messages
    before sending them to the LLM.
    """

    def __init__(self, *args, **kwargs):
        turn_off_logging()
        super().__init__(*args, **kwargs)
        # Browser-use may expect a 'model' attribute
        self.model = self.model_name

    def _call(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        turn_off_logging()
        result = super()._call(messages, stop, run_manager, **kwargs)
        return result

    async def _astream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[AsyncCallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> AsyncIterator[ChatGenerationChunk]:
        turn_off_logging()
        async for chunk in super()._astream(messages, stop, run_manager, **kwargs):
            yield chunk


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
        # Apply rate limiting if configured
        apply_rate_limiter_sync(self.a0_model_conf, " ".join(texts))

        resp = embedding(model=self.model_name, input=texts, **self.kwargs)
        return [
            item.get("embedding") if isinstance(item, dict) else item.embedding  # type: ignore
            for item in resp.data  # type: ignore
        ]

    def embed_query(self, text: str) -> List[float]:
        # Apply rate limiting if configured
        apply_rate_limiter_sync(self.a0_model_conf, text)

        resp = embedding(model=self.model_name, input=[text], **self.kwargs)
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


def _parse_chunk(chunk: Any) -> ChatChunk:
    delta = chunk["choices"][0].get("delta", {})
    message = chunk["choices"][0].get("message", {}) or chunk["choices"][0].get(
        "model_extra", {}
    ).get("message", {})
    response_delta = (
        delta.get("content", "")
        if isinstance(delta, dict)
        else getattr(delta, "content", "")
    ) or (
        message.get("content", "")
        if isinstance(message, dict)
        else getattr(message, "content", "")
    )
    reasoning_delta = (
        delta.get("reasoning_content", "")
        if isinstance(delta, dict)
        else getattr(delta, "reasoning_content", "")
    )

    return ChatChunk(reasoning_delta=reasoning_delta, response_delta=response_delta)



def _adjust_call_args(provider_name: str, model_name: str, kwargs: dict):
    # for openrouter add app reference
    if provider_name == "openrouter":
        kwargs["extra_headers"] = {
            "HTTP-Referer": "https://agent-zero.ai",
            "X-Title": "Agent Zero",
        }

    # remap other to openai for litellm
    if provider_name == "other":
        provider_name = "openai"

    return provider_name, model_name, kwargs


def _merge_provider_defaults(
    provider_type: str, original_provider: str, kwargs: dict
) -> tuple[str, dict]:
    # Normalize .env-style numeric strings (e.g., "timeout=30") into ints/floats for LiteLLM
    def _normalize_values(values: dict) -> dict:
        result: dict[str, Any] = {}
        for k, v in values.items():
            if isinstance(v, str):
                try:
                    result[k] = int(v)
                except ValueError:
                    try:
                        result[k] = float(v)
                    except ValueError:
                        result[k] = v
            else:
                result[k] = v
        return result

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

    # Merge LiteLLM global kwargs (timeouts, stream_timeout, etc.)
    try:
        global_kwargs = settings.get_settings().get("litellm_global_kwargs", {})  # type: ignore[union-attr]
    except Exception:
        global_kwargs = {}
    if isinstance(global_kwargs, dict):
        for k, v in _normalize_values(global_kwargs).items():
            kwargs.setdefault(k, v)

    return provider_name, kwargs


def get_chat_model(
    provider: str, name: str, model_config: Optional[ModelConfig] = None, **kwargs: Any
) -> LiteLLMChatWrapper:
    orig = provider.lower()
    provider_name, kwargs = _merge_provider_defaults("chat", orig, kwargs)
    return _get_litellm_chat(
        LiteLLMChatWrapper, name, provider_name, model_config, **kwargs
    )


def get_browser_model(
    provider: str, name: str, model_config: Optional[ModelConfig] = None, **kwargs: Any
) -> BrowserCompatibleChatWrapper:
    orig = provider.lower()
    provider_name, kwargs = _merge_provider_defaults("chat", orig, kwargs)
    return _get_litellm_chat(
        BrowserCompatibleChatWrapper, name, provider_name, model_config, **kwargs
    )


def get_embedding_model(
    provider: str, name: str, model_config: Optional[ModelConfig] = None, **kwargs: Any
) -> LiteLLMEmbeddingWrapper | LocalSentenceTransformerWrapper:
    orig = provider.lower()
    provider_name, kwargs = _merge_provider_defaults("embedding", orig, kwargs)
    return _get_litellm_embedding(name, provider_name, model_config, **kwargs)
