from helpers.history import output_langchain, output_text, output_text_for_summary
from langchain_core.messages import AIMessage, HumanMessage


def test_output_langchain_omits_leading_assistant_messages():
    messages = output_langchain(
        [
            {"ai": True, "content": "Welcome"},
            {"ai": False, "content": "Hello"},
            {"ai": True, "content": "Hi"},
        ]
    )

    assert messages == [HumanMessage("Hello"), AIMessage("Hi")]


def test_output_text_for_summary_flattens_assistant_tool_protocol():
    messages = [
        {"ai": False, "content": "Check the database connection."},
        {
            "ai": True,
            "content": (
                '{"thoughts":["Inspect credentials"],'
                '"headline":"Checking database configuration",'
                '"tool_name":"code_execution_tool",'
                '"tool_args":{"runtime":"terminal","code":"psql -l"}}'
            ),
        },
    ]

    raw = output_text(messages, ai_label="assistant", human_label="user")
    summary = output_text_for_summary(
        messages, ai_label="assistant", human_label="user"
    )

    assert '"thoughts"' in raw
    assert '"tool_args"' in raw
    assert summary == (
        "user: Check the database connection.\n"
        "assistant: Checking database configuration (tool: code_execution_tool)"
    )
    assert "Inspect credentials" not in summary
    assert "psql -l" not in summary


def test_output_text_for_summary_keeps_final_response_text():
    messages = [
        {
            "ai": True,
            "content": (
                '{"thoughts":["Done"],"headline":"Responding",'
                '"tool_name":"response","tool_args":{"text":"The fix is ready."}}'
            ),
        }
    ]

    assert output_text_for_summary(messages) == "ai: The fix is ready."


def test_output_text_for_summary_preserves_plain_assistant_content():
    messages = [{"ai": True, "content": "A plain assistant response."}]

    assert output_text_for_summary(messages) == "ai: A plain assistant response."
