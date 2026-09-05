from types import SimpleNamespace

from plugins._context_doctor.extensions.python.message_loop_result._10_context_doctor import (
    ContextDoctor,
)
from plugins._context_doctor.helpers.context_doctor import (
    looks_like_tool_call,
    transform_response,
    update_log_item,
)


def test_repairs_and_minifies_tool_call():
    response = '{"tool_name":"response","tool_args":{"text":"ok",},}'

    assert transform_response(response, suppress_xml=True) == (
        '{"tool_name":"response","tool_args":{"text":"ok"}}'
    )


def test_chooses_most_complete_tool_call():
    response = (
        '{"tool_name":"first","tool_args":{}} '
        '{"thoughts":["x"],"headline":"Second","tool_name":"second","tool_args":{"x":1}}'
    )

    assert transform_response(response, suppress_xml=True) == (
        '{"thoughts":["x"],"headline":"Second","tool_name":"second","tool_args":{"x":1}}'
    )


def test_wraps_raw_text_in_thoughts():
    assert transform_response("plain text", suppress_xml=True) == (
        '{"thoughts":["plain text"]}'
    )


def test_does_not_wrap_json_with_thoughts_or_headline():
    response = '{"thoughts":["Reasoning"],"headline":"A title"}'

    assert transform_response(response, suppress_xml=True) == response


def test_does_not_wrap_json_with_only_headline():
    response = '{"headline":"Just a headline"}'

    assert transform_response(response, suppress_xml=True) == response


def test_does_not_wrap_json_with_only_thoughts():
    response = '{"thoughts":["only thoughts"]}'

    assert transform_response(response, suppress_xml=True) == response


def test_suppresses_xml_when_enabled():
    assert transform_response("<tool>response</tool>", suppress_xml=True) == "{}"
    assert transform_response("<tool>response</tool>", suppress_xml=False) == (
        '{"thoughts":["<tool>response</tool>"]}'
    )


def test_splits_blank_line_thoughts_after_repair():
    response = '{"thoughts":["first\\n\\nsecond"]}'

    assert transform_response(response, suppress_xml=True) == (
        '{"thoughts":["first","second"]}'
    )


def test_splits_blank_lines_in_raw_text_fallback():
    assert transform_response("first\n\nsecond", suppress_xml=False) == (
        '{"thoughts":["first","second"]}'
    )


def test_keeps_blank_line_thoughts_when_split_disabled():
    assert transform_response(
        "first\n\nsecond", suppress_xml=False, split_thoughts=False
    ) == '{"thoughts":["first\\n\\nsecond"]}'


def test_updates_log_kvps_and_heading_while_preserving_raw_content():
    log_item = SimpleNamespace(
        kvps={"reasoning": "because"},
        update=lambda **kwargs: setattr(log_item, "data", kwargs),
    )
    raw = '{"tool_name":"response","tool_args":{"text":"ok",},}'
    repaired = '{"headline":"Done","tool_name":"response","tool_args":{"text":"ok"}}'

    update_log_item(
        SimpleNamespace(agent_name="A0"),
        log_item,
        repaired,
        update_log=False,
        raw_response=raw,
    )

    assert log_item.data["content"] == raw
    assert log_item.data["kvps"]["reasoning"] == "because"
    assert log_item.data["kvps"]["tool_name"] == "response"
    assert log_item.data["heading"] == "A0: Done"


def test_converted_to_thoughts_rejects_plain_text_wrap():
    assert not looks_like_tool_call("plain text", '{"thoughts":["plain text"]}')


def test_converted_to_thoughts_rejects_split_multi_paragraph_wrap():
    response = "first\n\nsecond"
    transformed = '{"thoughts":["first","second"]}'
    assert not looks_like_tool_call(response, transformed)


def test_transform_and_fallback_agree_on_multi_paragraph_raw_text():
    response = "first\n\nsecond"
    transformed = transform_response(response, suppress_xml=False)
    assert not looks_like_tool_call(response, transformed)


def test_converted_to_thoughts_detects_native_thoughts_json():
    response = '{"thoughts":["only thoughts"]}'

    assert looks_like_tool_call(response, response)


def test_looks_like_tool_call_detects_tool_calls():
    response = '{"tool_name":"response","tool_args":{"text":"ok"}}'

    assert looks_like_tool_call(response, response)


def test_looks_like_tool_call_rejects_empty_dict():
    assert not looks_like_tool_call("<x>y</x>", "{}")


def test_looks_like_tool_call_rejects_non_a0_dict():
    assert not looks_like_tool_call('{"foo":"bar"}', '{"foo":"bar"}')


def test_looks_like_tool_call_rejects_empty_thoughts_list():
    assert not looks_like_tool_call('{"thoughts":[]}', '{"thoughts":[]}')


def test_looks_like_tool_call_rejects_blank_thoughts_entries():
    assert not looks_like_tool_call('{"thoughts":["","  "]}', '{"thoughts":["","  "]}')


def test_looks_like_tool_call_rejects_empty_headline():
    assert not looks_like_tool_call('{"headline":""}', '{"headline":""}')


def test_looks_like_tool_call_rejects_empty_tool_name():
    assert not looks_like_tool_call('{"tool_name":""}', '{"tool_name":""}')


def test_looks_like_tool_call_rejects_empty_tool_args():
    assert not looks_like_tool_call('{"tool_args":{}}', '{"tool_args":{}}')


def test_looks_like_tool_call_rejects_wrong_thoughts_type():
    assert not looks_like_tool_call('{"thoughts":"x"}', '{"thoughts":"x"}')


def test_extension_replaces_result_refreshes_log_and_response_item(monkeypatch):
    monkeypatch.setattr(
        "plugins._context_doctor.extensions.python.message_loop_result._10_context_doctor.get_plugin_config",
        lambda *args, **kwargs: {"suppress_xml": True, "update_log": False},
    )
    llm_result = SimpleNamespace(
        response='{"tool_name":"response","tool_args":{"text":"ok",},}'
    )
    log_item = SimpleNamespace(
        id="generating", update=lambda **kwargs: setattr(log_item, "data", kwargs)
    )
    response_item = SimpleNamespace(
        update=lambda **kwargs: setattr(response_item, "data", kwargs)
    )
    context = SimpleNamespace(log=SimpleNamespace(log=lambda **kwargs: response_item))
    agent = SimpleNamespace(
        agent_name="A0",
        context=context,
        loop_data=SimpleNamespace(params_temporary={"log_item_generating": log_item}),
    )

    ContextDoctor(agent).execute({"llm_result": llm_result})

    assert llm_result.response == '{"tool_name":"response","tool_args":{"text":"ok"}}'
    assert log_item.data["content"] != llm_result.response
    assert log_item.data["kvps"]["tool_name"] == "response"
    assert response_item.data == {"content": "ok"}


def test_extension_does_not_create_response_item_for_other_tools(monkeypatch):
    monkeypatch.setattr(
        "plugins._context_doctor.extensions.python.message_loop_result._10_context_doctor.get_plugin_config",
        lambda *args, **kwargs: {"suppress_xml": True, "update_log": False},
    )
    log_item = SimpleNamespace(id="generating", update=lambda **kwargs: None)
    agent = SimpleNamespace(
        agent_name="A0",
        context=SimpleNamespace(log=SimpleNamespace(log=lambda **kwargs: None)),
        loop_data=SimpleNamespace(params_temporary={"log_item_generating": log_item}),
    )
    llm_result = SimpleNamespace(
        response='{"tool_name":"notify_user","tool_args":{"message":"not final"}}'
    )

    ContextDoctor(agent).execute({"llm_result": llm_result})

    assert "log_item_response" not in agent.loop_data.params_temporary


def test_extension_does_not_use_legacy_response_message_key(monkeypatch):
    monkeypatch.setattr(
        "plugins._context_doctor.extensions.python.message_loop_result._10_context_doctor.get_plugin_config",
        lambda *args, **kwargs: {"suppress_xml": True, "update_log": False},
    )
    log_item = SimpleNamespace(id="generating", update=lambda **kwargs: None)
    agent = SimpleNamespace(
        agent_name="A0",
        context=SimpleNamespace(log=SimpleNamespace(log=lambda **kwargs: None)),
        loop_data=SimpleNamespace(params_temporary={"log_item_generating": log_item}),
    )
    llm_result = SimpleNamespace(
        response='{"tool_name":"response","tool_args":{"message":"not final"}}'
    )

    ContextDoctor(agent).execute({"llm_result": llm_result})

    assert "log_item_response" not in agent.loop_data.params_temporary


def test_extension_handles_raw_text_fallback_with_warning_and_skip(monkeypatch):
    monkeypatch.setattr(
        "plugins._context_doctor.extensions.python.message_loop_result._10_context_doctor.get_plugin_config",
        lambda *args, **kwargs: {"suppress_xml": True, "update_log": False},
    )
    log_item = SimpleNamespace(
        id="generating", kvps={"reasoning": "thinking"},
        update=lambda **kwargs: setattr(log_item, "data", kwargs),
    )
    logs = []
    warnings = []
    ai_responses = []
    agent = SimpleNamespace(
        agent_name="A0",
        context=SimpleNamespace(log=SimpleNamespace(log=lambda **kwargs: logs.append(kwargs))),
        loop_data=SimpleNamespace(params_temporary={"log_item_generating": log_item}),
        read_prompt=lambda name, **kwargs: {
            "fw.msg_thoughts_fallback.md": "fallback warning",
            "fw.msg_thoughts_fallback_response.md": "fallback notice",
        }[name],
        hist_add_ai_response=lambda message, **kwargs: ai_responses.append(message) or SimpleNamespace(id="ai"),
        hist_add_warning=lambda message: warnings.append(message) or SimpleNamespace(id="warning"),
    )
    llm_result = SimpleNamespace(response="Hello there…")
    result_data = {"llm_result": llm_result}

    ContextDoctor(agent).execute(result_data)

    assert result_data["skip_default_processing"] is True
    assert llm_result.response == '{"thoughts":["Hello there…"]}'
    assert ai_responses == ['{"thoughts":["Hello there…"]}']
    assert warnings == ["fallback warning"]
    assert logs[0]["content"] == "A0: fallback notice"
    assert logs[0]["id"] == "warning"
    assert log_item.data["kvps"]["reasoning"] == "thinking"
    assert log_item.data["content"] == "Hello there…"
