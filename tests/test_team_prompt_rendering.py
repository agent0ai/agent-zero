from types import SimpleNamespace

from helpers import files, team_access


def test_team_prompt_values_are_inserted_literally(tmp_path):
    (tmp_path / "layout.md").write_text(
        '{{member_text}}\n{{ include "footer.md" }}', encoding="utf-8",
    )
    (tmp_path / "footer.md").write_text("Trusted template footer", encoding="utf-8")
    context = SimpleNamespace(get_data={team_access.CHAT_PROJECT_ID: "team-project"}.get)
    agent = SimpleNamespace(context=context)
    value = 'Document the syntax {{ include "footer.md" }} and {{member_text}}.'

    rendered = files.read_prompt_file("layout.md", [str(tmp_path)], _agent=agent, member_text=value)

    assert rendered == f"{value}\nTrusted template footer"


def test_team_json_prompt_keeps_values_with_braces_and_quotes(tmp_path):
    (tmp_path / "message.md").write_text(
        '```json\n{"message": {{message}}, "type": {{type}}}\n```', encoding="utf-8",
    )
    context = SimpleNamespace(get_data={team_access.CHAT_PROJECT_ID: "team-project"}.get)
    agent = SimpleNamespace(context=context)
    text = 'Keep "{{type}}" as part of the note.'

    rendered = files.parse_file("message.md", [str(tmp_path)], _agent=agent, message=text, type="user")

    assert rendered == {"message": text, "type": "user"}
