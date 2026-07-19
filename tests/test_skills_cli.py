from helpers import skills, skills_cli


def test_cli_uses_runtime_skill_contract(monkeypatch, tmp_path):
    monkeypatch.setattr(
        skills_cli.files,
        "get_abs_path",
        lambda *parts: str(tmp_path.joinpath(*parts)),
    )
    skill_dir = skills_cli.create_skill(
        "cli-contract",
        "Use this skill to verify the shared CLI and runtime contract.",
    )
    skills_root = tmp_path / "usr" / "skills"
    monkeypatch.setattr(skills, "get_skill_roots", lambda agent=None: [str(skills_root)])

    parsed = skills_cli.parse_skill_file(skill_dir / "SKILL.md")

    assert isinstance(parsed, skills.Skill)
    assert parsed.triggers == ["cli-contract"]
    assert skills_cli.get_skills_dirs() == [skills_root]
    assert [skill.name for skill in skills_cli.list_skills()] == ["cli-contract"]
    assert skills_cli.find_skill("cli-contract").triggers == ["cli-contract"]
    assert [skill.name for skill in skills_cli.search_skills("cli-contract")] == [
        "cli-contract"
    ]
    assert skills_cli.validate_skill(parsed) == skills.validate_skill(parsed) == []

    invalid_dir = skills_root / "invalid-skill"
    invalid_dir.mkdir()
    (invalid_dir / "SKILL.md").write_text(
        "---\nname: invalid-skill\n---\n\n# Invalid skill\n",
        encoding="utf-8",
    )
    invalid = skills_cli.find_skill("invalid-skill")

    assert invalid is not None
    assert skills_cli.validate_skill(invalid) == ["Missing required field: description"]
