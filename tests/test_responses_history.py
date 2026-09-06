from copy import deepcopy
import json

import pytest

from helpers import responses_history as history
from helpers.llm_result import LLMResult
from helpers.litellm_transport import LiteLLMTransport, clear_transport_capability_cache


TOOLS = [{"type": "function", "name": "lookup", "parameters": {"type": "object", "properties": {}}}]
BASE = [{"role": "system", "content": "Rules"}, {"role": "user", "content": "Question"}]


@pytest.fixture(autouse=True)
def clear_capabilities():
    clear_transport_capability_cache()


def render(record):
    value = record["content"]
    return json.dumps(value, separators=(",", ":")) if isinstance(value, dict) else value


def transport(prompt, prefix, records=(), **kwargs):
    return LiteLLMTransport(model=kwargs.pop("model", "openai/test"), messages=prompt, kwargs={
        "a0_api_mode": "responses", "responses_state": "local",
        "a0_responses_function_tools": TOOLS,
        "responses_history_context": {
            "prompt": prompt, "prefix": prefix,
            "groups": history.prepare_groups(list(records), render, lambda text: text),
        }, **kwargs,
    })


def completed_call(source, call_id="call_1", name="lookup"):
    request = source._responses_request(stream=False)
    return source._llm_result_from_response({"id": "resp_1", "output": [
        {"type": "reasoning", "id": "rs_" + call_id, "encrypted_content": "opaque", "summary": []},
        {"type": "function_call", "id": "fc_" + call_id, "call_id": call_id, "name": name, "arguments": '{"q":"a0"}'},
    ]}, request)


def records_for(result):
    return [
        {"ai": True, "content": result.function_calls_text(), "metadata": result.metadata()},
        {"ai": False, "content": {"tool_name": "lookup", "tool_result": "Found", "file": "/visible/file.txt"}, "metadata": {
            "responses": {"input_items": [{"type": "function_call_output", "call_id": result.function_calls[0].call_id, "output": "DO NOT REPLAY RAW OUTPUT"}]},
        }},
    ]


def prompt_for(records, base=None):
    return [*(base or BASE), {"role": "assistant", "content": render(records[0])},
            {"role": "user", "content": render(records[1]) + "\nCurrent extras"}]


def test_native_replay_uses_visible_results_and_retains_current_extras():
    source = transport([BASE[0], {"role": "user", "content": "Question\nOld extras"}], BASE)
    result = completed_call(source)
    records = records_for(result)
    original = deepcopy(records)
    prompt = prompt_for(records)
    replay = transport(prompt, prompt, records)
    request = replay._responses_request(stream=False)
    assert request["input"][:2] == BASE
    assert request["input"][2:4] == [item.to_dict() for item in result.output_items]
    assert request["input"][4] == {"type": "function_call_output", "call_id": "call_1", "output": render(records[1])}
    assert request["input"][5] == {"role": "user", "content": "Current extras"}
    assert "DO NOT REPLAY RAW OUTPUT" not in json.dumps(request)
    assert "Old extras" not in json.dumps(request)
    assert "responses_history_context" not in request
    assert records == original
    assert prompt == prompt_for(records)


def test_prepared_context_lifecycle_and_post_hook_changes(monkeypatch):
    from types import SimpleNamespace
    from langchain_core.messages import SystemMessage, HumanMessage
    from langchain_core.prompts import ChatPromptTemplate
    from agent import Agent, LoopData
    from models import LiteLLMChatWrapper
    from helpers import secrets

    agent = object.__new__(Agent)
    agent.context = SimpleNamespace()
    agent.loop_data = LoopData()
    model = LiteLLMChatWrapper(model="test", provider="openai", model_config=None)
    prompt = [SystemMessage("Rules"), HumanMessage("Question")]
    monkeypatch.setattr(secrets, "get_secrets_manager", lambda _: SimpleNamespace(mask_values=lambda text: text))
    history.remember_prompt(agent.loop_data, ChatPromptTemplate.from_messages(prompt).format(), prompt[0], [])
    call = {"model": model, "messages": prompt, "responses_prompt_replacements": {"Rules": "Override"}}
    prepared = history.prepare_call(agent, call)
    assert prepared["responses_history_context"]["prompt"] == BASE
    assert prepared["responses_prompt_replacements"] == {"Rules": "Override"}
    for changed in (
        [SystemMessage("Changed by hook"), prompt[1]],
        [SystemMessage("Rules", additional_kwargs={"provider_control": True}), prompt[1]],
    ):
        assert "responses_history_context" not in history.prepare_call(agent, {**call, "messages": changed})
    agent.loop_data.params_temporary["responses_prompt_replacements"] = {"stale": "value"}
    history.start_prompt(agent.loop_data)
    assert history.prepare_call(agent, {"model": model, "messages": prompt}) == {"responses_prompt_replacements": {}}


@pytest.mark.parametrize("change", ["summary", "arguments", "missing_output", "wrong_id", "attachments", "commentary", "unencrypted", "legacy", "secret"])
def test_ineligible_history_stays_in_prepared_text(change):
    result = completed_call(transport(BASE, BASE))
    records = records_for(result)
    base = deepcopy(BASE)
    mask = lambda text: text
    if change == "summary":
        base[1]["content"] = "Compressed question"
    elif change == "arguments":
        records[0]["content"] = records[0]["content"].replace('a0', 'MASKED')
    elif change == "missing_output":
        records[1]["metadata"] = {}
    elif change == "wrong_id":
        records[1]["metadata"]["responses"]["input_items"][0]["call_id"] = "other"
    elif change == "attachments":
        records[1]["content"] = [{"type": "input_image", "image_url": "data:image/png;base64,AAAA"}]
    elif change == "commentary":
        records[0]["metadata"]["responses"]["output_items"].append({"type": "message", "content": [{"type": "output_text", "text": "second tool call"}]})
    elif change == "unencrypted":
        records[0]["metadata"]["responses"]["output_items"][0].pop("encrypted_content")
    elif change == "legacy":
        records[0]["metadata"]["responses"]["capability"].pop(history.PREFIX_HASH)
    elif change == "secret":
        mask = lambda text: text.replace("opaque", "MASKED")
    prompt = [*base, {"role": "assistant", "content": render(records[0])}, {"role": "user", "content": render(records[1])}]
    groups = history.prepare_groups(records, render, mask)
    replay = transport(prompt, prompt)
    replay.kwargs["responses_history_context"]["groups"] = groups
    assert replay._responses_request(stream=False)["input"] == prompt


@pytest.mark.parametrize("kwargs", [
    {"model": "openai/other"}, {"api_base": "https://other.invalid"},
    {"a0_responses_function_tools": [{**TOOLS[0], "description": "new policy"}]},
])
def test_replay_is_bound_to_current_model_endpoint_and_tool_scope(kwargs):
    records = records_for(completed_call(transport(BASE, BASE)))
    prompt = prompt_for(records)
    replay = transport(prompt, prompt, records, **kwargs)
    assert replay._responses_request(stream=False)["input"] == prompt


def test_final_response_call_without_result_is_never_fabricated():
    result = completed_call(transport(BASE, BASE), name="response")
    assert history.prepare_groups(records_for(result)[:1], render, lambda text: text) == []


def test_chat_request_drops_replay_control_and_keeps_text_examples():
    records = records_for(completed_call(transport(BASE, BASE)))
    prompt = prompt_for(records)
    replay = transport(prompt, prompt, records, a0_api_mode="chat")
    request = replay._chat_request(stream=False)
    assert request["messages"] == prompt
    assert "responses_history_context" not in request
    assert "tools" not in request
    assert history.PREFIX_HASH not in replay._capability_metadata()


def test_changed_selected_input_cannot_acquire_a_history_digest():
    replay = transport(BASE, BASE, responses_local_input_items=[{"role": "user", "content": "override"}])
    assert replay._responses_request(stream=False)["input"] == [{"role": "user", "content": "override"}]
    assert history.PREFIX_HASH not in replay._capability_metadata()


@pytest.mark.parametrize("duplicate", [False, True])
def test_multiple_groups_preserve_history_order_without_duplicate_native_ids(duplicate):
    first = records_for(completed_call(transport(BASE, BASE)))
    second_prompt = prompt_for(first)
    second_prefix = deepcopy(second_prompt)
    second_prefix[-1]["content"] = render(first[1])
    second = records_for(completed_call(transport(second_prompt, second_prefix, first), call_id="call_1" if duplicate else "call_2"))
    records = first + second
    prompt = [*second_prefix, *prompt_for(second)[len(BASE):]]
    replay = transport(prompt, prompt, records)
    request = replay._responses_request(stream=False)
    calls = [item for item in request["input"] if item.get("type") == "function_call"]
    assert [item["call_id"] for item in calls] == (["call_1"] if duplicate else ["call_1", "call_2"])
    assert request["input"][-1]["content"].endswith("Current extras")


def test_masking_failure_disables_native_projection():
    records = records_for(completed_call(transport(BASE, BASE)))
    def unavailable(text):
        raise OSError("masking unavailable")
    assert history.prepare_groups(records, render, unavailable) == []


@pytest.mark.asyncio
async def test_automatic_chat_fallback_keeps_text_and_drops_history_controls(monkeypatch):
    from helpers import litellm_transport
    records = records_for(completed_call(transport(BASE, BASE)))
    prompt = prompt_for(records)
    calls = []
    class BadRequestError(RuntimeError):
        pass
    async def responses(**kwargs):
        calls.append("responses")
        assert any(item.get("type") == "function_call" for item in kwargs["input"])
        assert "responses_history_context" not in kwargs
        raise BadRequestError("Cannot determine type of item")
    async def chat(**kwargs):
        calls.append("chat")
        assert kwargs["messages"] == prompt
        assert "responses_history_context" not in kwargs
        assert "tools" not in kwargs
        return {"choices": [{"message": {"content": "fallback"}}]}
    monkeypatch.setattr(litellm_transport, "aresponses", responses)
    monkeypatch.setattr(litellm_transport, "acompletion", chat)
    replay = transport(prompt, prompt, records)
    await replay.acomplete()
    assert calls == ["responses", "chat"]
    assert history.PREFIX_HASH not in replay.last_result.capability
    assert replay.last_result.mode == "chat_completions"


def test_tool_result_summary_is_replayed_as_visible_summary_only():
    records = records_for(completed_call(transport(BASE, BASE)))
    records[1]["content"] = "Condensed tool result"
    prompt = prompt_for(records)
    replay = transport(prompt, prompt, records)
    request = replay._responses_request(stream=False)
    output = next(item for item in request["input"] if item.get("type") == "function_call_output")
    assert output["output"] == "Condensed tool result"
    assert "DO NOT REPLAY RAW OUTPUT" not in json.dumps(request)
