from typing import Any, List, Optional
import litellm
from litellm import acompletion
from langchain_core.callbacks.manager import CallbackManagerForLLMRun
from langchain_core.messages import BaseMessage

import models
from browser_use.llm import ChatGoogle, ChatOpenRouter

from plugins._browser_agent.helpers import browser_use_monkeypatch
from plugins._browser_agent.helpers import browser_use_openrouter_compat
from plugins._browser_agent.helpers import browser_use_output_sanitize


_BROWSER_USE_PATCHED = False


def apply_browser_use_patches() -> None:
    global _BROWSER_USE_PATCHED
    if _BROWSER_USE_PATCHED:
        return

    browser_use_monkeypatch.apply()
    litellm.modify_params = True
    _BROWSER_USE_PATCHED = True


class AsyncAIChatReplacement:
    class _Completions:
        def __init__(self, wrapper):
            self._wrapper = wrapper

        async def create(self, *args, **kwargs):
            return await self._wrapper._acall(*args, **kwargs)

    class _Chat:
        def __init__(self, wrapper):
            self.completions = AsyncAIChatReplacement._Completions(wrapper)

    def __init__(self, wrapper, *args, **kwargs):
        self._wrapper = wrapper
        self.chat = AsyncAIChatReplacement._Chat(wrapper)


class BrowserCompatibleChatWrapper(ChatOpenRouter):
    """
    A wrapper for browser agent that can filter/sanitize messages
    before sending them to the LLM.
    """

    def __init__(self, *args, **kwargs):
        apply_browser_use_patches()
        models.turn_off_logging()
        self._wrapper = models.LiteLLMChatWrapper(*args, **kwargs)
        self.model = self._wrapper.model_name
        self.kwargs = self._wrapper.kwargs

    @property
    def model_name(self) -> str:
        return self._wrapper.model_name

    @property
    def provider(self) -> str:
        return self._wrapper.provider

    def get_client(self, *args, **kwargs):  # type: ignore
        return AsyncAIChatReplacement(self, *args, **kwargs)

    async def _acall(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ):
        models.apply_rate_limiter_sync(self._wrapper.a0_model_conf, str(messages))

        try:
            model = kwargs.pop("model", None)
            effective_model = model or self._wrapper.model_name
            kwrgs = {**self._wrapper.kwargs, **kwargs}
            request_messages = messages

            # hack from browser-use to fix json schema for gemini (additionalProperties, $defs, $ref)
            if "response_format" in kwrgs and "json_schema" in kwrgs["response_format"] and effective_model and effective_model.startswith("gemini/"):
                kwrgs["response_format"]["json_schema"] = ChatGoogle("")._fix_gemini_schema(kwrgs["response_format"]["json_schema"])

            if browser_use_openrouter_compat.should_use_openrouter_prompt_schema_fallback(
                    provider=self.provider,
                    model_name=effective_model,
                    kwargs=kwrgs,
                ):
                fallback_request = browser_use_openrouter_compat.build_json_object_fallback_request(
                    messages=messages,
                    kwargs=kwrgs,
                )
                if fallback_request is not None:
                    request_messages, kwrgs = fallback_request

            resp = await acompletion(
                model=self._wrapper.model_name,
                messages=request_messages,
                stop=stop,
                **kwrgs,
            )

            # Gemini: strip triple backticks and conform schema
            try:
                msg = resp.choices[0].message # type: ignore
                if self.provider == "gemini" and isinstance(getattr(msg, "content", None), str):
                    cleaned = browser_use_monkeypatch.gemini_clean_and_conform(msg.content) # type: ignore
                    if cleaned:
                        msg.content = cleaned
            except Exception:
                pass

        except Exception as e:
            raise e

        # Structured output: normalize keys/models reject (e.g. "" on action dicts) and repair partial JSON
        try:
            rf = kwrgs.get("response_format") or {}
            if "json_schema" in rf or "json_object" in rf:
                msg_obj = resp.choices[0].message
                raw_content = getattr(msg_obj, "content", None)
                fixed = browser_use_output_sanitize.sanitize_llm_message_content_for_browser_use(raw_content)  # type: ignore[arg-type]
                if fixed is not None:
                    msg_obj.content = fixed
        except Exception:
            pass

        return resp


def build_browser_model_from_config(
    model_config: models.ModelConfig,
) -> BrowserCompatibleChatWrapper:
    apply_browser_use_patches()
    original_provider = model_config.provider.lower()
    provider_name, kwargs = models._merge_provider_defaults(  # type: ignore[attr-defined]
        "chat", original_provider, model_config.build_kwargs()
    )
    return models._get_litellm_chat(  # type: ignore[attr-defined]
        BrowserCompatibleChatWrapper,
        model_config.name,
        provider_name,
        model_config,
        **kwargs,
    )

def build_browser_model_for_agent(agent=None) -> BrowserCompatibleChatWrapper:
    """Build and return the browser-use adapter using chat model config."""
    from plugins._model_config.helpers.model_config import (
        get_chat_model_config,
        build_model_config,
    )
    import models
    
    cfg = get_chat_model_config(agent)
    mc = build_model_config(cfg, models.ModelType.CHAT)
    return build_browser_model_from_config(mc)
