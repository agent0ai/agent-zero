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


@pytest.mark.parametrize("content, comment", [
    ("TOKEN=abc#synthetic-tail", ""),
    ("TOKEN=#synthetic-tail", ""),
    ("TOKEN= #synthetic-tail", ""),
    ('TOKEN=abc"def"#synthetic-tail', ""),
    ("TOKEN=abc'def'#synthetic-tail", ""),
    ("TOKEN=abc # note", " # note"),
    ("TOKEN='a#b'# note", " # note"),
    ('TOKEN="q" # note', " # note"),
    (r'TOKEN="a\"#b"# note', " # note"),
    ('TOKEN="first\n#second" # note', " # note"),
    ("export TOKEN = value # note", " # note"),
    ("'TOKEN'=value # note", " # note"),
])
def test_secret_comments_follow_dotenv_parsing(tmp_path, content, comment):
    path = tmp_path / "secrets.env"
    path.write_text(content)
    manager = secrets.SecretsManager(str(path))
    original = manager.parse_env_content(content)

    assert manager.get_secrets_for_prompt() == "§§secret(TOKEN)" + comment
    masked = manager.get_masked_secrets()
    assert masked == 'TOKEN="***"' + comment
    manager.save_secrets_with_merge(masked)
    assert manager.parse_env_content(path.read_text()) == original


@pytest.mark.parametrize("malformed", ['BAD="synthetic-unterminated', "bad key=synthetic-value"])
@pytest.mark.parametrize("runtime_file", [False, True])
def test_secret_prompt_excludes_malformed_values(tmp_path, monkeypatch, malformed, runtime_file):
    path = tmp_path / "secrets.env"
    path.write_text("API_KEY_GOOD=synthetic-good\n" + malformed)
    if runtime_file:
        monkeypatch.setattr(secrets.dotenv, "get_dotenv_file_path", lambda: str(path))
    manager = secrets.SecretsManager(str(path))

    assert manager.get_secrets_for_prompt() == "§§secret(API_KEY_GOOD)"
    assert malformed in manager.get_masked_secrets()


@pytest.mark.parametrize("failure", ["permission", "encoding"])
def test_secret_read_failures_do_not_empty_the_store_or_cache(tmp_path, monkeypatch, failure):
    path = tmp_path / "secrets.env"
    original = b"TOKEN=synthetic-existing-value\n"
    stored = original + b"# invalid UTF-8: \xff\n" if failure == "encoding" else original
    path.write_bytes(stored)
    manager = secrets.SecretsManager(str(path))

    with monkeypatch.context() as patch:
        if failure == "permission":
            def unreadable(*args, **kwargs):
                raise PermissionError("synthetic read failure")
            patch.setattr(secrets.files, "read_file", unreadable)

        for submitted in ('TOKEN="***"\n', "NEW=synthetic-new-value\n", ""):
            with pytest.raises(secrets.RepairableException):
                manager.save_secrets_with_merge(submitted)
            assert path.read_bytes() == stored

        for read in (manager.read_secrets_raw, manager.get_masked_secrets, manager.load_secrets):
            with pytest.raises(secrets.RepairableException):
                read()

        with pytest.raises(secrets.RepairableException):
            manager.save_secrets_with_merge('TOKEN="***"\n')
        assert path.read_bytes() == stored

    path.write_bytes(original)
    assert manager.load_secrets() == {"TOKEN": "synthetic-existing-value"}


def test_masked_save_preserves_a_value_rotated_since_read(tmp_path):
    path = tmp_path / "secrets.env"
    path.write_text("TOKEN=synthetic-old-value\n")
    manager = secrets.SecretsManager(str(path))
    masked = manager.get_masked_secrets()
    path.write_text("TOKEN=synthetic-rotated-value\n")

    manager.save_secrets_with_merge(masked)

    assert manager.parse_env_content(path.read_text()) == {"TOKEN": "synthetic-rotated-value"}


def test_masked_editor_hides_a_shadowed_value(tmp_path):
    path = tmp_path / "secrets.env"
    path.write_text("TOKEN=synthetic-shadowed-value\nTOKEN=\n")
    manager = secrets.SecretsManager(str(path))

    masked = manager.get_masked_secrets()
    assert masked == 'TOKEN="***"\nTOKEN=""'
    manager.save_secrets_with_merge(masked)
    assert manager.parse_env_content(path.read_text()) == {"TOKEN": ""}


@pytest.mark.parametrize("chunk_size", range(1, len("synthetic-token") + 1))
def test_streaming_secrets_are_masked_across_chunk_boundaries(chunk_size):
    value = "synthetic-token"
    stream = secrets.StreamingSecretsFilter({"TOKEN": value})
    output = "".join(
        stream.process_chunk(value[start:start + chunk_size])
        for start in range(0, len(value), chunk_size)
    ) + stream.finalize()

    assert output == "§§secret(TOKEN)"
    assert stream.finalize() == ""


@pytest.mark.parametrize("text, expected", [
    ("ordinary text", "ordinary text"),
    ("This is", "This is"),
    ("tail sy", "tail sy"),
    ("tail syn", "tail ***"),
])
def test_streaming_short_prefixes_preserve_the_final_mask_threshold(text, expected):
    stream = secrets.StreamingSecretsFilter({"TOKEN": "synthetic-token"})

    assert "".join(stream.process_chunk(char) for char in text) + stream.finalize() == expected


@pytest.mark.parametrize("reload_env", [False, True])
def test_dotenv_writes_refresh_all_secret_managers(tmp_path, monkeypatch, reload_env):
    path = tmp_path / "runtime.env"
    key = "API_KEY_SECRET_TEST"
    path.write_text(f"{key}=synthetic-old-value\n")
    monkeypatch.setenv(key, "synthetic-old-value")
    monkeypatch.setattr(secrets.dotenv, "get_dotenv_file_path", lambda: str(path))
    monkeypatch.setattr(secrets.SecretsManager, "_instances", {})
    managers = [
        secrets.SecretsManager.get_instance(str(path)),
        secrets.SecretsManager.get_instance(str(tmp_path / "global.env"), str(path)),
    ]
    for manager in managers:
        assert manager.load_secrets()[key] == "synthetic-old-value"

    for value in ("synthetic-new-value", ""):
        secrets.dotenv.save_dotenv_value(key, value, reload_env=reload_env)
        for manager in managers:
            assert manager.replace_placeholders(secrets.alias_for_key(key)) == value
            assert (secrets.alias_for_key(key) in manager.get_secrets_for_prompt()) == bool(value)
            if value:
                assert manager.mask_values(value) == secrets.alias_for_key(key)
        expected_env = value if reload_env else "synthetic-old-value"
        assert secrets.dotenv.get_dotenv_value(key) == expected_env


@pytest.mark.parametrize("key", ["API_KEY_TEST_PROVIDER", "TEST_PROVIDER_API_KEY", "TEST_PROVIDER_API_TOKEN"])
@pytest.mark.parametrize("pool", ["synthetic-first,synthetic-second", " synthetic-first, , synthetic-second , "])
def test_provider_key_pools_mask_each_key_without_changing_stored_values(tmp_path, monkeypatch, key, pool):
    path = tmp_path / "runtime.env"
    path.write_text(f'{key}={json.dumps(pool)}\n')
    monkeypatch.setattr(secrets.dotenv, "get_dotenv_file_path", lambda: str(path))
    manager = secrets.SecretsManager(str(path))
    alias = secrets.alias_for_key(key)

    assert manager.replace_placeholders(alias) == pool
    assert manager.mask_values(pool) == alias
    assert manager.mask_values("keys: synthetic-first / synthetic-second.") == f"keys: {alias} / {alias}."
    assert manager.mask_values("synthetic-first", placeholder="<{key}>") == f"<{key}>"
    assert manager.get_secrets_for_prompt() == alias
    assert manager.load_secrets() == {key: pool}

    text = "keys: synthetic-first / synthetic-second."
    for chunk_size in (1, 2, 7, len(text)):
        stream = manager.create_streaming_filter()
        output = "".join(
            stream.process_chunk(text[start:start + chunk_size])
            for start in range(0, len(text), chunk_size)
        ) + stream.finalize()
        assert output == f"keys: {alias} / {alias}."


def test_commas_in_ordinary_secrets_do_not_create_individual_secrets(tmp_path):
    path = tmp_path / "secrets.env"
    value = "first-word,second-word"
    path.write_text(f"PASSWORD={value}\n")
    manager = secrets.SecretsManager(str(path))
    text = f"first-word / second-word / {value}."
    expected = "first-word / second-word / §§secret(PASSWORD)."

    assert manager.mask_values(text) == expected
    stream = manager.create_streaming_filter()
    assert "".join(stream.process_chunk(char) for char in text) + stream.finalize() == expected


def test_provider_key_pool_members_respect_the_text_mask_length_threshold(tmp_path):
    path = tmp_path / "secrets.env"
    path.write_text("API_KEY_TEST_PROVIDER=abc,def\n")
    manager = secrets.SecretsManager(str(path))

    assert manager.mask_values("abc / def") == "abc / def"
    assert manager.mask_values("abc / def", min_length=3) == (
        "§§secret(API_KEY_TEST_PROVIDER) / §§secret(API_KEY_TEST_PROVIDER)"
    )
