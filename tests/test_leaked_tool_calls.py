import json
from pathlib import Path

import pytest

from helpers.extract_tools import extract_leaked_tool_request, extract_tool_request


DSML_COMMAND = "cd /a0/usr/projects/disko && git log --oneline -15 && echo '=STATUS=' && git status --porcelain | head -5 && echo '=BRANCH=' && git branch --show-current"
DSML_ARGS = {"runtime": "terminal", "session": 0, "reset": False, "code": DSML_COMMAND}
DSML_EXAMPLE = (
    '<｜DSML｜ calls> <｜DSML｜ invoke name="code_execution_tool"> '
    '<｜DSML｜ parameter name="tool_args" string="false">'
    + json.dumps(DSML_ARGS)
    + '</｜DSML｜ parameter> </｜DSML｜ invoke> </｜DSML｜ calls>'
)


def test_recovers_reported_dsml_envelope_without_changing_arguments():
    assert extract_tool_request(DSML_EXAMPLE) is None
    assert extract_leaked_tool_request(DSML_EXAMPLE) == (
        "call", {"tool_name": "code_execution_tool", "tool_args": DSML_ARGS}
    )


def test_recovers_reported_dsml_parallel_call_with_headline():
    text = Path(__file__).with_name("fixtures").joinpath("dsml_parallel_headline.txt").read_text()
    args = json.loads(text.split('string="false">', 1)[1].split('</｜DSML｜ parameter>', 1)[0])
    assert extract_tool_request(text) is None
    assert extract_leaked_tool_request(text) == ("call", {
        "tool_name": "parallel",
        "tool_args": args,
        "headline": "Reading the project file and searching for a relevant implementation",
    })


@pytest.mark.parametrize("headline", [None, "Read file"])
def test_recovers_reported_dsml_with_repeated_tool_name(headline):
    text = Path(__file__).with_name("fixtures").joinpath("dsml_text_editor_tool_name.txt").read_text()
    expected = {
        "tool_name": "text_editor",
        "tool_args": {"action": "read", "path": "/a0/usr/projects/test/about-v3.md"},
    }
    if headline is not None:
        text = text.replace('</｜DSML｜ invoke>',
            f'<｜DSML｜ parameter name="headline" string="true">{headline}</｜DSML｜ parameter></｜DSML｜ invoke>')
        expected["headline"] = headline

    assert extract_tool_request(text) is None
    assert extract_leaked_tool_request(text) == ("call", expected)


@pytest.mark.parametrize("wrap", [
    lambda body: f'<｜DSML｜ calls><｜DSML｜ invoke name="x">{body}</｜DSML｜ invoke></｜DSML｜ calls>',
    lambda body: f'<｜DSML｜function_calls><｜DSML｜invoke name="x">{body}</｜DSML｜invoke></｜DSML｜function_calls>',
])
def test_dsml_parameters_preserve_string_flags_and_json_types(wrap):
    body = (
        '<｜DSML｜ parameter name="text" string="true">  true\n & <tag>  </｜DSML｜ parameter>'
        '<｜DSML｜ parameter name="data" string="false"> {"nested": [true, null, 2]} </｜DSML｜ parameter>'
        '<｜DSML｜ parameter name="headline" string="true">An ordinary tool argument</｜DSML｜ parameter>'
        '<｜DSML｜ parameter name="tool_name" string="true">Another tool argument</｜DSML｜ parameter>'
    )
    assert extract_leaked_tool_request(wrap(body)) == (
        "call", {"tool_name": "x", "tool_args": {"text": "  true\n & <tag>  ", "data": {"nested": [True, None, 2]}, "headline": "An ordinary tool argument", "tool_name": "Another tool argument"}}
    )


@pytest.mark.parametrize("body", [
    '<｜DSML｜ parameter name="tool_args" string="false">[]</｜DSML｜ parameter>',
    '<｜DSML｜ parameter name="tool_args" string="true">{}</｜DSML｜ parameter>',
    '<｜DSML｜ parameter name="a" string="false">{"x":1,"x":2}</｜DSML｜ parameter>',
    '<｜DSML｜ parameter name="a" string="false">NaN</｜DSML｜ parameter>',
    '<｜DSML｜ parameter name="a" string="false">1e999</｜DSML｜ parameter>',
    '<｜DSML｜ parameter name="a" string="false">{"x":1,}</｜DSML｜ parameter>',
    '<｜DSML｜ parameter name="a" string="false">{"x":</｜DSML｜ parameter>',
    '<｜DSML｜ parameter name="a">1</｜DSML｜ parameter>',
    '<｜DSML｜ parameter name="a" string="maybe">1</｜DSML｜ parameter>',
    '<｜DSML｜ parameter name="a" string="false">1</｜DSML｜ parameter>' * 2,
    '<｜DSML｜ parameter name="tool_args" string="false">{}</｜DSML｜ parameter>'
    '<｜DSML｜ parameter name="extra" string="false">1</｜DSML｜ parameter>',
    '<｜DSML｜ parameter name="tool_args" string="false">{}</｜DSML｜ parameter>'
    '<｜DSML｜ parameter name="headline" string="false">{}</｜DSML｜ parameter>',
    '<｜DSML｜ parameter name="tool_args" string="false">{}</｜DSML｜ parameter>'
    '<｜DSML｜ parameter name="headline" string="true">One</｜DSML｜ parameter>'
    '<｜DSML｜ parameter name="headline" string="true">Two</｜DSML｜ parameter>',
    '<｜DSML｜ parameter name="tool_args" string="false">{}</｜DSML｜ parameter>'
    '<｜DSML｜ parameter name="tool_name" string="true">different_tool</｜DSML｜ parameter>',
    '<｜DSML｜ parameter name="tool_args" string="false">{}</｜DSML｜ parameter>'
    '<｜DSML｜ parameter name="tool_name" string="false">{}</｜DSML｜ parameter>',
    '<｜DSML｜ parameter name="tool_args" string="false">{}</｜DSML｜ parameter>'
    '<｜DSML｜ parameter name="tool_name" string="true">x</｜DSML｜ parameter>'
    '<｜DSML｜ parameter name="tool_name" string="true">x</｜DSML｜ parameter>',
    'unparsed text',
])
def test_dsml_rejects_ambiguous_or_invalid_parameters(body):
    text = f'<｜DSML｜ calls><｜DSML｜ invoke name="x">{body}</｜DSML｜ invoke></｜DSML｜ calls>'
    assert extract_leaked_tool_request(text) == ("rejected", None)


@pytest.mark.parametrize("text,status", [
    (DSML_EXAMPLE + DSML_EXAMPLE, "rejected"),
    ("Example: " + DSML_EXAMPLE, "rejected"),
    (DSML_EXAMPLE + " explanation", "rejected"),
    (f"```xml\n{DSML_EXAMPLE}\n```", "quoted"),
    (f"Use `{DSML_EXAMPLE}` as an example.", "quoted"),
    (DSML_EXAMPLE[:100], "truncated"),
    ('<｜DSML｜ calls>', "truncated"),
    ('<｜DSML｜ calls><｜DSML｜ invoke name="x"></｜DSML｜ invoke>'
     '<｜DSML｜ invoke name="x"></｜DSML｜ invoke></｜DSML｜ calls>', "rejected"),
])
def test_dsml_rejects_multiple_partial_and_quoted_calls(text, status):
    assert extract_leaked_tool_request(text) == (status, None)


@pytest.mark.parametrize(
    "text",
    [
        '<tool_call>{"name":"x","arguments":{"a":1}}</tool_call>',
        '<tool_call>[{"name":"x","parameters":{"a":1}}]</tool_call>',
        '<tool_call>{"tool_name":"x","tool_args":{"a":1}}</tool_call>',
        "<function=x><parameter=a>1</parameter></function>",
        "<tool_call><function=x><parameter=a>1</parameter></function></tool_call>",
        '{"name":"x","arguments":{"a":1}}',
        '{"name":"x","arguments":"{\\"a\\":1}"}',
    ],
)
def test_recovers_one_complete_call(text):
    assert extract_tool_request(text) is None
    status, request = extract_leaked_tool_request(text)
    assert status == "call"
    assert request == {"tool_name": "x", "tool_args": {"a": 1}}


@pytest.mark.parametrize("wrap", [lambda text: text, lambda text: f"<tool_call>{text}</tool_call>"])
@pytest.mark.parametrize("headline", [None, "Outer headline"])
def test_leaked_json_keeps_outer_headline_without_promoting_nested_fields(wrap, headline):
    args = {"headline": "Argument headline", "nested": {"headline": "Nested headline"}}
    source = {"name": "x", "arguments": args}
    expected = {"tool_name": "x", "tool_args": args}
    if headline is not None:
        source["headline"] = headline
        expected["headline"] = headline

    assert extract_leaked_tool_request(wrap(json.dumps(source))) == ("call", expected)


def test_keeps_provider_names_for_authorization_at_the_result_hook():
    status, request = extract_leaked_tool_request(
        '{"name":"native_x:read","arguments":{"path":"notes"}}'
    )
    assert status == "call"
    assert request == {"tool_name": "native_x:read", "tool_args": {"path": "notes"}}


@pytest.mark.parametrize(
    "text",
    [
        "<tool_call",
        "<tool_call>",
        "<function=x",
        "<function=x><parameter=path>/tmp/half",
        '<tool_call>{"name":"x","arguments":{}}',
        '<tool_call>{"name":"x","arguments":{}}</tool_call',
        '<tool_call>{"name":"x","arguments":{"path":"half',
        '{"name":"x","arguments":{"path":"half',
        '{"tool_name":"x","tool_args":{"path":"half',
    ],
)
def test_truncated_calls_never_produce_a_request(text):
    status, request = extract_leaked_tool_request(text)
    assert status == "truncated"
    assert request is None


@pytest.mark.parametrize(
    "text",
    [
        '<tool_call>{"name":"x","arguments":[]}</tool_call>',
        '<tool_call>{"name":"x","arguments":null}</tool_call>',
        '<tool_call>{"name":"x","arguments":{"a":1,}}</tool_call>',
        '<tool_call>{"name":"x","name":"response","arguments":{}}</tool_call>',
        '<tool_call>{"name":"x","arguments":{"a":1,"a":2}}</tool_call>',
        '<tool_call>{"name":"x","arguments":{"a":NaN}}</tool_call>',
        '<tool_call>{"name":"x","arguments":{"a":1e999}}</tool_call>',
        '{"name":"x","arguments":{},"parameters":{}}',
        '<tool_call>{"tool_name":"x","tool_args":{},"name":"response"}</tool_call>',
        "<function=x><parameter=a>one</parameter><parameter=a>two</parameter></function>",
        "<function=x><parameter=a>half</function>",
        "<function=x>unparsed<parameter=a>1</parameter></function>",
        "<function=x><parameter=a><function=x></parameter></function>",
        '<function_calls><invoke name="x"></invoke></function_calls>',
        "<minimax:tool_call>anything</minimax:tool_call>",
        "<|tool_calls_section_begin|>anything",
    ],
)
def test_rejects_malformed_ambiguous_and_unsupported_calls(text):
    status, request = extract_leaked_tool_request(text)
    assert status == "rejected"
    assert request is None


@pytest.mark.parametrize(
    "wrap",
    [
        lambda call: f"Example: {call}",
        lambda call: f"{call} and then explain it",
        lambda call: call + call,
        lambda call: call + "<function=x>",
        lambda call: f"```text\nexample\n```\n{call}",
    ],
)
def test_does_not_execute_a_call_amid_prose_or_other_calls(wrap):
    status, request = extract_leaked_tool_request(
        wrap('<tool_call>{"name":"x","arguments":{}}</tool_call>')
    )
    assert status == "rejected"
    assert request is None


@pytest.mark.parametrize(
    "wrap",
    [
        lambda call: f"Example:\n```xml\n{call}\n```",
        lambda call: f"~~~xml\n{call}\n~~~",
        lambda call: f"````xml\n{call}\n````",
        lambda call: f"Use `{call}` to call a tool.",
        lambda call: f"Use ``{call}`` to call a tool.",
        lambda call: f"```xml\n{call}",
    ],
)
def test_quoted_tool_examples_are_not_calls(wrap):
    status, request = extract_leaked_tool_request(
        wrap('<tool_call>{"name":"x","arguments":{}}</tool_call>')
    )
    assert status == "quoted"
    assert request is None


def test_preserves_json_string_payload_including_fences_and_markup():
    text = 'Example: ```json\n{"name":"x","arguments":{}}\n``` </tool_call> { \\"'
    status, request = extract_leaked_tool_request(
        "<tool_call>"
        + json.dumps({"name": "response", "arguments": {"text": text}})
        + "</tool_call>"
    )
    assert request["tool_args"]["text"] == text


def test_xml_parameters_preserve_whitespace_and_coerce_only_intact_tokens():
    status, request = extract_leaked_tool_request(
        '<function=x><parameter=data>{"a":1}</parameter>'
        "<parameter=text>  hello world\n</parameter><parameter=enabled>true</parameter>"
        "<parameter=content>```python\nprint(1)\n```</parameter></function>"
    )
    assert request["tool_args"] == {
        "data": {"a": 1},
        "text": "  hello world\n",
        "enabled": True,
        "content": "```python\nprint(1)\n```",
    }


@pytest.mark.parametrize(
    "text",
    [
        "Plain answer.",
        '{"name":"ordinary data"}',
        '{"text":"<tool_call>this is data</tool_call>"}',
        '{"thoughts":[],"tool_name":"response","tool_args":{"text":"<tool_call>example</tool_call>"}}',
        '{"type":"function","name":"x","parameters":{}}',
    ],
)
def test_clean_and_canonical_responses_keep_existing_behavior(text):
    assert extract_leaked_tool_request(text)[0] == "clean"


def test_multiple_native_calls_are_rejected_as_a_whole():
    status, request = extract_leaked_tool_request(
        '[{"name":"x","arguments":{}},{"name":"response","arguments":{}}]'
    )
    assert status == "rejected"
    assert request is None


@pytest.mark.parametrize(
    "text",
    [
        "{'tool_name':'x','tool_args':{}} {'tool_name':'response','tool_args':{}}",
        '{tool_name:"x",tool_args:{}} {tool_name:"response",tool_args:{}}',
    ],
)
def test_multiple_dirty_canonical_calls_cannot_reach_plugin_repair(text):
    assert extract_leaked_tool_request(text)[0] == "rejected"
