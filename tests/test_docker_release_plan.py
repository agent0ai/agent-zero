import importlib.util
import subprocess
import sys
from pathlib import Path

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = PROJECT_ROOT / ".github" / "scripts" / "docker_release_plan.py"


def load_module():
    spec = importlib.util.spec_from_file_location("docker_release_plan", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def commit_file(repo: Path, name: str, content: str, message: str) -> str:
    (repo / name).write_text(content, encoding="utf-8")
    git(repo, "add", name)
    git(repo, "commit", "-m", message)
    return git(repo, "rev-parse", "HEAD")


def seed_remote_refs(repo: Path, *branches: str) -> None:
    for branch in branches:
        git(repo, "update-ref", f"refs/remotes/origin/{branch}", git(repo, "rev-parse", branch))


def test_docker_publish_workflow_tracks_branch_promotions():
    workflow_path = PROJECT_ROOT / ".github" / "workflows" / "docker-publish.yml"
    content = workflow_path.read_text(encoding="utf-8")

    assert 'branches:\n      - "testing"\n      - "ready"\n      - "main"\n    tags:' in content
    assert 'ALLOWED_BRANCHES: "testing ready main"' in content
    assert 'tags:\n      - "v*"' in content
    assert "workflow_dispatch:" in content
    assert "inputs:" in content
    assert "tag:" in content
    assert "SOURCE_REF_TYPE: ${{ github.ref_type }}" in content
    assert "BEFORE_SHA: ${{ github.event_name == 'push' && github.event.before || '' }}" in content


def test_plan_branch_push_builds_when_tag_reaches_allowed_branch(monkeypatch, tmp_path: Path):
    release_plan = load_module()

    git(tmp_path, "init", "-b", "main")
    git(tmp_path, "config", "user.name", "Test User")
    git(tmp_path, "config", "user.email", "test@example.com")

    commit_file(tmp_path, "README.md", "base\n", "base")
    git(tmp_path, "tag", "v1.6")
    git(tmp_path, "branch", "testing")

    git(tmp_path, "checkout", "-b", "development")
    git(tmp_path, "checkout", "main")
    git(tmp_path, "merge", "--ff-only", "development")

    git(tmp_path, "checkout", "development")
    commit_file(tmp_path, "feature.txt", "release\n", "release v1.7")
    git(tmp_path, "tag", "v1.7")

    testing_before = git(tmp_path, "rev-parse", "testing")
    git(tmp_path, "checkout", "testing")
    git(tmp_path, "merge", "--no-ff", "development", "-m", "promote v1.7 to testing")

    git(tmp_path, "checkout", "main")
    git(tmp_path, "merge", "--no-ff", "development", "-m", "promote v1.7 to main")
    seed_remote_refs(tmp_path, "testing", "main")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("ALLOWED_BRANCHES", "testing main")
    monkeypatch.setenv("MAIN_BRANCH", "main")
    monkeypatch.setenv("DOCKER_IMAGE_REPO", "example/agent-zero")
    monkeypatch.setenv("RELEASE_TAG_REGEX", r"^v([0-9]+)\.([0-9]+)$")
    monkeypatch.setenv("MIN_RELEASE_MAJOR", "1")
    monkeypatch.setenv("MIN_RELEASE_MINOR", "0")
    monkeypatch.setenv("EVENT_NAME", "push")
    monkeypatch.setenv("SOURCE_REF_TYPE", "branch")
    monkeypatch.setenv("MANUAL_TAG", "")
    monkeypatch.setenv("AFTER_SHA", git(tmp_path, "rev-parse", "testing"))

    monkeypatch.setenv("SOURCE_REF_NAME", "testing")
    monkeypatch.setenv("BEFORE_SHA", testing_before)
    config = release_plan.load_config()
    branch_states = release_plan.collect_branch_states(config)
    testing_candidates, testing_notes = release_plan.plan_branch_push(config, branch_states)

    assert testing_notes == []
    assert len(testing_candidates) == 1
    assert testing_candidates[0].branch == "testing"
    assert testing_candidates[0].source_tag == "v1.7"
    assert testing_candidates[0].mode == "push_promoted_tag"
    assert testing_candidates[0].publish_version is False
    assert testing_candidates[0].publish_branch_tag is True

    monkeypatch.setenv("SOURCE_REF_NAME", "main")
    monkeypatch.setenv("BEFORE_SHA", git(tmp_path, "rev-list", "--max-parents=0", "HEAD"))
    monkeypatch.setenv("AFTER_SHA", git(tmp_path, "rev-parse", "main"))
    config = release_plan.load_config()
    branch_states = release_plan.collect_branch_states(config)
    main_candidates, main_notes = release_plan.plan_branch_push(config, branch_states)

    assert main_notes == []
    assert len(main_candidates) == 1
    assert main_candidates[0].branch == "main"
    assert main_candidates[0].source_tag == "v1.7"
    assert main_candidates[0].mode == "push_promoted_tag"
    assert main_candidates[0].publish_version is True
    assert main_candidates[0].publish_branch_tag is True


def test_preview_only_publishes_the_newest_tag_reachable_from_v3(monkeypatch, tmp_path):
    workflow = yaml.load(
        (PROJECT_ROOT / ".github/workflows/docker-v3.yml").read_text(), Loader=yaml.BaseLoader
    )
    assert workflow["on"] == {"push": {"tags": ["pre-v3.[0-9]+"]}}
    jobs = workflow["jobs"]
    command = next(step["run"] for step in jobs["check"]["steps"] if step.get("id") == "check")
    assert jobs["build"]["if"] == "needs.check.outputs.eligible == 'true'"
    assert jobs["publish"]["needs"] == "build"
    assert '--tag "$IMAGE:v3"' in jobs["publish"]["steps"][-1]["run"]
    git(tmp_path, "init", "-b", "main")
    git(tmp_path, "config", "user.name", "Test User")
    git(tmp_path, "config", "user.email", "test@example.com")
    commit_file(tmp_path, "base", "base", "stable")
    git(tmp_path, "tag", "v2.16")
    git(tmp_path, "checkout", "-b", "v3")
    commit_file(tmp_path, "feature", "one", "first preview")
    git(tmp_path, "tag", "pre-v3.2")
    commit_file(tmp_path, "feature", "two", "next preview")
    git(tmp_path, "tag", "-a", "pre-v3.10", "-m", "preview")
    git(tmp_path, "branch", "-f", "main", "v3")
    seed_remote_refs(tmp_path, "main", "v3")
    git(tmp_path, "checkout", "main")
    commit_file(tmp_path, "only-main", "three", "unrelated")
    git(tmp_path, "tag", "pre-v3.11")

    output = tmp_path / "output"
    monkeypatch.setenv("GITHUB_OUTPUT", str(output))
    for tag, expected in [("pre-v3.10", True), ("pre-v3.2", False), ("pre-v3.11", False), ("v2.16", False)]:
        git(tmp_path, "checkout", "--detach", tag)
        output.write_text("")
        monkeypatch.setenv("GITHUB_REF_NAME", tag)
        subprocess.run(["bash", "-eo", "pipefail", "-c", command], cwd=tmp_path, check=True)
        assert (output.read_text().strip() == "eligible=true") is expected
