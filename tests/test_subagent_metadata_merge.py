from pathlib import Path

from helpers import subagents


def _write_profile(root: Path, name: str, metadata: str = "") -> Path:
    profile = root / name
    profile.mkdir(parents=True)
    if metadata:
        (profile / "agent.yaml").write_text(metadata, encoding="utf-8")
    return profile


def test_missing_metadata_inherits_and_present_empty_clears(tmp_path: Path) -> None:
    bundled_root = tmp_path / "agents"
    user_root = tmp_path / "usr-agents"
    _write_profile(
        bundled_root,
        "researcher",
        "title: Researcher\ndescription: Source heavy\ncontext: Delegate research\n",
    )
    _write_profile(user_root, "researcher", "description: ''\ncontext: ''\n")

    bundled = subagents._load_agent_data_from_dir(
        str(bundled_root), "researcher", "default"
    )
    user = subagents._load_agent_data_from_dir(
        str(user_root), "researcher", "user"
    )
    merged = subagents._merge_agent(bundled, user)

    assert merged is not None
    assert merged.title == "Researcher"
    assert merged.description == ""
    assert merged.context == ""
    assert merged.origin == ["default", "user"]


def test_prompt_only_override_does_not_clear_metadata(tmp_path: Path) -> None:
    bundled_root = tmp_path / "agents"
    user_root = tmp_path / "usr-agents"
    _write_profile(
        bundled_root,
        "researcher",
        "title: Researcher\ndescription: Source heavy\ncontext: Delegate research\n",
    )
    profile = _write_profile(user_root, "researcher")
    prompts = profile / "prompts"
    prompts.mkdir()
    (prompts / "agent.system.main.specifics.md").write_text(
        "Only this changes.\n", encoding="utf-8"
    )

    merged = subagents._merge_agent(
        subagents._load_agent_data_from_dir(
            str(bundled_root), "researcher", "default"
        ),
        subagents._load_agent_data_from_dir(
            str(user_root), "researcher", "user"
        ),
    )

    assert merged is not None
    assert merged.title == "Researcher"
    assert merged.description == "Source heavy"
    assert merged.context == "Delegate research"
    assert merged.prompts == {
        "agent.system.main.specifics.md": "Only this changes.\n"
    }


def test_nonexistent_layer_is_not_an_override(tmp_path: Path) -> None:
    assert (
        subagents._load_agent_data_from_dir(str(tmp_path), "missing", "user")
        is None
    )


def test_default_specifics_uses_only_the_canonical_prompt_path() -> None:
    root = Path(__file__).resolve().parents[1]
    legacy = root / "agents" / "default" / "agent.system.main.specifics.md"
    canonical = (
        root
        / "agents"
        / "default"
        / "prompts"
        / "agent.system.main.specifics.md"
    )

    assert not legacy.exists()
    assert canonical.is_file()
    assert canonical.read_bytes() == b""
