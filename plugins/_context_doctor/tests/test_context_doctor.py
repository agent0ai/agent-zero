from types import SimpleNamespace

from plugins._context_doctor.extensions.python.message_loop_result._10_context_doctor import (
    ContextDoctor,
)
from plugins._context_doctor.helpers.context_doctor import (
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
