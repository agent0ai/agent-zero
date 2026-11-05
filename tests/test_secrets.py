import json
import os

import pytest

from helpers import secrets
from helpers.errors import RepairableException


class _Context:
    def get_data(self, key: str):
        return None


class _ProjectContext:
    def __init__(self, project):
        self._project = project

    def get_data(self, key: str):
        if key == "project":
            return self._project
        return None


def _two_project_contents(parent):
    return {
        "usr/secrets.env": "GLOBAL_KEY=dummy-global-value-111\n",
        "usr/.env": (
            "API_KEY_OPENAI=dummy-llm-value-222\n"
            "ANONYMIZED_TELEMETRY=false\n"
        ),
        os.path.join(parent, "ProjectA", ".a0proj", "secrets.env"): (
            "API_TOKEN=dummy-a-value-111\n"
            "SHARED_KEY=dummy-shared-a\n"
            "X_ONLY=dummy-x-only-value\n"
        ),
        os.path.join(parent, "ProjectB", ".a0proj", "secrets.env"): (
            "API_TOKEN=dummy-b-value-222\n"
            "SHARED_KEY=dummy-shared-b\n"
            "OTHER=dummy-b-other\n"
        ),
    }


@pytest.fixture
def _two_projects(tmp_path, monkeypatch):
    parent = str(tmp_path / "projects")
    for name in ("ProjectA", "ProjectB"):
        os.makedirs(os.path.join(parent, name, ".a0proj"), exist_ok=True)
    from helpers import projects

    monkeypatch.setattr(projects, "get_projects_parent_folder", lambda: parent)
    monkeypatch.setattr(secrets.SecretsManager, "_instances", {})
    monkeypatch.setattr(secrets.dotenv, "get_dotenv_file_path", lambda: "usr/.env")
    monkeypatch.setattr(
        secrets.files, "read_file", _two_project_contents(parent).__getitem__
    )
    return parent


def test_masking_manager_masks_sibling_project_secrets(_two_projects):
    masker = secrets.get_secrets_masking_manager(_ProjectContext("ProjectB"))
    text = "leaked dummy-a-value-111 and dummy-b-value-222 and dummy-global-value-111"
    masked = masker.mask_values(text)
    assert "dummy-a-value-111" not in masked
    assert "dummy-b-value-222" not in masked
    assert "dummy-global-value-111" not in masked
    assert masked.count("***") == 3


def test_masking_manager_masks_both_values_for_duplicate_key(_two_projects):
    # ProjectA and ProjectB share the key API_TOKEN with different values.
    # A merged dict would keep only one; the masking facility must mask both.
    masker = secrets.get_secrets_masking_manager(_ProjectContext("ProjectB"))
    assert "dummy-a-value-111" not in masker.mask_values("x dummy-a-value-111 y")
    assert "dummy-b-value-222" not in masker.mask_values("x dummy-b-value-222 y")


def test_masking_manager_uses_generic_placeholder_not_alias(_two_projects):
    masker = secrets.get_secrets_masking_manager(_ProjectContext("ProjectB"))
    masked = masker.mask_values("token dummy-a-value-111 here")
    assert "§§secret(" not in masked
    assert masked == "token *** here"


def test_masking_manager_empty_values_do_not_corrupt_text(_two_projects, monkeypatch):
    masker = secrets.get_secrets_masking_manager(_ProjectContext("ProjectB"))
    assert masker.mask_values("ordinary text, nothing secret") == (
        "ordinary text, nothing secret"
    )


def test_masking_streaming_filter_masks_sibling_value_across_chunks(_two_projects):
    masker = secrets.get_secrets_masking_manager(_ProjectContext("ProjectB"))
    stream_filter = masker.create_streaming_filter()
    out = stream_filter.process_chunk("prefix dummy-b-val")
    out += stream_filter.process_chunk("ue-222 suffix")
    out += stream_filter.finalize()
    assert "dummy-b-value-222" not in out
    assert "***" in out


def test_resolution_manager_never_resolves_sibling_project_placeholder(_two_projects):
    manager = secrets.get_secrets_manager(_ProjectContext("ProjectB"))
    # Own + global placeholders still resolve.
    assert manager.replace_placeholders("§§secret(API_TOKEN)") == "dummy-b-value-222"
    assert manager.replace_placeholders("§§secret(GLOBAL_KEY)") == "dummy-global-value-111"
    # A key that exists ONLY in ProjectA must not resolve under ProjectB.
    with pytest.raises(RepairableException) as excinfo:
        manager.replace_placeholders("§§secret(X_ONLY)")
    assert "dummy-x-only-value" not in str(excinfo.value)


def test_project_secrets_manager_isolation_maintained(_two_projects):
    manager = secrets.get_project_secrets_manager("ProjectA")
    loaded = manager.load_secrets()
    assert loaded["API_TOKEN"] == "dummy-a-value-111"
    assert "OTHER" not in loaded
    assert "X_ONLY" in loaded


def test_get_project_names_lists_sorted_projects(tmp_path, monkeypatch):
    from helpers import projects

    parent = tmp_path / "projects"
    for name in ("Zulu", "Alpha", ".hidden", "Beta"):
        (parent / name).mkdir(parents=True)
    monkeypatch.setattr(projects, "get_projects_parent_folder", lambda: str(parent))
    assert projects.get_project_names() == ["Alpha", "Beta", "Zulu"]


def test_get_project_names_missing_parent_folder_is_empty(tmp_path, monkeypatch):
    from helpers import projects

    monkeypatch.setattr(
        projects, "get_projects_parent_folder", lambda: str(tmp_path / "nope")
    )
    assert projects.get_project_names() == []


def test_get_project_names_skips_symlinked_project_dirs(tmp_path, monkeypatch):
    from helpers import projects

    parent = tmp_path / "projects"
    real = tmp_path / "outside"
    (parent / "Real").mkdir(parents=True)
    real.mkdir()
    os.symlink(str(real), str(parent / "Linked"))
    monkeypatch.setattr(projects, "get_projects_parent_folder", lambda: str(parent))
    assert projects.get_project_names() == ["Real"]


def test_sibling_secrets_path_guard_denies_other_project(_two_projects, tmp_path, monkeypatch):
    from helpers import projects

    monkeypatch.setattr(projects, "get_projects_parent_folder", lambda: _two_projects)
    ctx = _ProjectContext("ProjectB")
    denied = os.path.join(_two_projects, "ProjectA", ".a0proj", "secrets.env")
    assert secrets.is_sibling_project_secrets_path(denied, ctx) is True
    allowed = os.path.join(_two_projects, "ProjectB", ".a0proj", "secrets.env")
    assert secrets.is_sibling_project_secrets_path(allowed, ctx) is False
    # Traversal out of the active project still denied after normalization.
    traversal = os.path.join(
        _two_projects, "ProjectB", "..", "ProjectA", ".a0proj", "secrets.env"
    )
    assert secrets.is_sibling_project_secrets_path(traversal, ctx) is True
    # Ordinary project files are never denied.
    code = os.path.join(_two_projects, "ProjectA", "code.py")
    assert secrets.is_sibling_project_secrets_path(code, ctx) is False
    # With no active project, no project's secrets file is accessible.
    assert secrets.is_sibling_project_secrets_path(denied, _Context()) is True


def test_sibling_secrets_path_guard_denies_symlink_escape(tmp_path, monkeypatch):
    from helpers import projects

    parent = tmp_path / "projects"
    (parent / "ProjectA" / ".a0proj").mkdir(parents=True)
    (parent / "ProjectB").mkdir(parents=True)
    os.symlink(str(parent / "ProjectA"), str(parent / "ProjectB" / "link"))
    monkeypatch.setattr(projects, "get_projects_parent_folder", lambda: str(parent))
    ctx = _ProjectContext("ProjectB")
    escaped = os.path.join(parent, "ProjectB", "link", ".a0proj", "secrets.env")
    assert secrets.is_sibling_project_secrets_path(escaped, ctx) is True


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
