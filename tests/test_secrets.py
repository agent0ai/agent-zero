import json

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
    assert "ANONYMIZED_TELEMETRY" not in manager.get_secrets_for_prompt()

    stream_filter = manager.create_streaming_filter()
    assert stream_filter.process_chunk("avoid falsely accusing a utility") == (
        "avoid falsely accusing a utility"
    )
    assert stream_filter.finalize() == ""


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
