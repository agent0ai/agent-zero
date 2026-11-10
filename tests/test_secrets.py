import json
from pathlib import Path

import pytest

from helpers import secrets


class _Context:
    def get_data(self, key: str):
        return None


def test_agent_secret_manager_masks_runtime_credentials_only(monkeypatch):
    monkeypatch.setattr(secrets.SecretsManager, "_instances", {})
    monkeypatch.setattr(secrets.dotenv, "get_dotenv_file_path", lambda: "usr/.env")

    contents = {
        "usr/secrets.env": "PROJECT_SECRET=project-value\n",
        "usr/.env": (
            "API_KEY_OPENAI=llm-secret-value\n"
            'API_KEY_ANTHROPIC=""\n'
            "AUTH_LOGIN=\n"
            "ROOT_PASSWORD=generated-root-value\n"
            "ANONYMIZED_TELEMETRY=false\n"
            "DEFAULT_USER_TIMEZONE=Europe/Rome\n"
        ),
    }
    monkeypatch.setattr(secrets.files, "read_file", contents.__getitem__)

    manager = secrets.get_secrets_manager(_Context())

    assert manager.mask_values(
        "project-value; key=llm-secret-value; avoid falsely accusing a utility"
    ) == (
        "§§secret(PROJECT_SECRET); key=§§secret(API_KEY_OPENAI); "
        "avoid falsely accusing a utility"
    )
    prompt = manager.get_secrets_for_prompt()
    assert "§§secret(API_KEY_OPENAI)" in prompt
    assert "§§secret(ROOT_PASSWORD)" in prompt
    for key in ("API_KEY_ANTHROPIC", "AUTH_LOGIN", "ANONYMIZED_TELEMETRY"):
        assert key not in prompt

    stream_filter = manager.create_streaming_filter()
    assert stream_filter.process_chunk("avoid falsely accusing a utility") == (
        "avoid falsely accusing a utility"
    )
    assert stream_filter.finalize() == ""


@pytest.mark.parametrize("content", [
    "", "# Heading\n", "KEY=\n", 'KEY=""\n', "KEY=''\n", "KEY\n",
    "export KEY=\n", "KEY=   \n", '# Heading\nKEY="" # Inline\n',
])
def test_secret_prompt_omits_empty_values(tmp_path, content):
    path = tmp_path / "secrets.env"
    path.write_text(content)
    manager = secrets.SecretsManager(str(path))

    assert manager.get_secrets_for_prompt() == ""


@pytest.mark.parametrize("global_content, project_content, expected", [
    ("KEY=global-value\n", "key=\n", ""),
    ("key=\n", "KEY=project-value\n", "§§secret(KEY)"),
    (
        "key=global-value # Old\nOTHER=other-value # Other\n",
        "# Project\nKEY=project-value # New\n",
        "§§secret(OTHER) # Other\n\n# Project\n§§secret(KEY) # New",
    ),
])
def test_secret_prompt_respects_overrides(tmp_path, global_content, project_content, expected):
    paths = [tmp_path / "global.env", tmp_path / "project.env"]
    for path, content in zip(paths, (global_content, project_content)):
        path.write_text(content)
    manager = secrets.SecretsManager(*(str(path) for path in paths))

    assert manager.get_secrets_for_prompt() == expected
    value = manager.parse_env_content(project_content)["KEY"]
    assert manager.load_secrets()["KEY"] == value
    assert manager.replace_placeholders("§§secret(KEY)") == value
    assert [path.read_text() for path in paths] == [global_content, project_content]


@pytest.mark.parametrize("value", ["0", "false", "None", "   ", "first\nsecond"])
def test_secret_prompt_preserves_nonempty_literals(tmp_path, value):
    path = tmp_path / "secrets.env"
    path.write_text(f'KEY={json.dumps(value)}\n')
    manager = secrets.SecretsManager(str(path))

    assert manager.get_secrets_for_prompt() == "§§secret(KEY)"
    assert manager.replace_placeholders("§§secret(KEY)") == value


@pytest.mark.parametrize("content", ["", 'KEY=""\n', "KEY=synthetic-value\n"])
@pytest.mark.parametrize("variables", ["", "PLAIN=example"])
def test_secret_guidance_requires_available_aliases(tmp_path, content, variables):
    path = tmp_path / "secrets.env"
    path.write_text(content)
    manager = secrets.SecretsManager(str(path))
    prompt = secrets.files.read_prompt_file(
        "agent.system.secrets.md",
        _directories=[str(Path(__file__).resolve().parents[1] / "prompts")],
        secrets=manager.get_secrets_for_prompt(),
        vars=variables,
    )

    available = bool(manager.load_secrets().get("KEY"))
    assert ("## secret aliases" in prompt) == available
    if available:
        assert prompt.lstrip("\n").startswith(
            "## secret aliases\n"
            "use exact alias form `§§secret(name)`; real values are injected automatically\n"
            "only use provided aliases; do not expose or invent secret values\n"
            "values may contain special characters, so quote or escape them correctly in shell or code\n"
            "comments help explain each secret's purpose\n"
        )
    else:
        assert "use exact alias form" not in prompt
    assert ("§§secret(KEY)" in prompt) == available
    assert ("## variables" in prompt) == bool(variables)
    assert "synthetic-value" not in prompt
    assert "{{" not in prompt


@pytest.mark.parametrize("value", [
    'value with "quotes" and # inside',
    r"C:\new\folder\test",
    r"literal \n and \t",
    "first\nsecond",
    "first\r\nsecond",
    "first\rsecond",
    "value\twith tab",
    "caffè 😀",
    "",
])
def test_secret_values_survive_save_and_masked_round_trip(tmp_path, monkeypatch, value):
    monkeypatch.setattr(secrets.SecretsManager, "_instances", {})
    manager = secrets.SecretsManager.get_instance(str(tmp_path / "secrets.env"))
    submitted = f'# Heading\nVALUE={json.dumps(value, ensure_ascii=False)} # Inline\n\nEMPTY=""\n'
    assert manager.parse_env_content(submitted) == {"VALUE": value, "EMPTY": ""}

    manager.save_secrets_with_merge(submitted)
    assert manager.load_secrets() == {"VALUE": value, "EMPTY": ""}

    masked = manager.get_masked_secrets()
    manager.save_secrets_with_merge(masked)
    assert manager.load_secrets() == {"VALUE": value, "EMPTY": ""}
    assert manager.get_masked_secrets() == masked
    assert "# Heading" in masked and "# Inline" in masked


@pytest.mark.parametrize("stored_key, submitted_key", [
    ("lower_secret", "LOWER_SECRET"),
    ("Mixed_Secret", "mixed_SECRET"),
    ("UPPER_SECRET", "upper_secret"),
])
def test_masked_secret_merge_uses_case_insensitive_keys(tmp_path, monkeypatch, stored_key, submitted_key):
    monkeypatch.setattr(secrets.SecretsManager, "_instances", {})
    path = tmp_path / "secrets.env"
    path.write_text(f'{stored_key}="original-value" # Keep\nREMOVE="remove-me"\n')
    manager = secrets.SecretsManager.get_instance(str(path))
    masked = manager.get_masked_secrets().replace(stored_key.upper(), submitted_key)

    manager.save_secrets_with_merge(masked)
    assert manager.load_secrets() == {stored_key.upper(): "original-value", "REMOVE": "remove-me"}
    assert "# Keep" in manager.read_secrets_raw()

    manager.save_secrets_with_merge(f'{submitted_key}=""\nNEW="***"\n# Edited')
    assert manager.load_secrets() == {stored_key.upper(): ""}
    assert "# Edited" in manager.read_secrets_raw()
