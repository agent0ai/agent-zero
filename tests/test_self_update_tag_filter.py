import sys
import types
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

sys.modules["giturlparse"] = types.SimpleNamespace(parse=lambda *args, **kwargs: None)

from helpers import self_update


def test_self_update_selector_tags_use_two_segments_and_v1_floor():
    assert self_update.is_valid_selector_tag("v1.0")
    assert self_update.is_valid_selector_tag("v12.34")
    assert self_update.is_valid_selector_tag("v0.9")
    assert self_update._is_selector_supported_tag("v1.0")
    assert self_update._is_selector_supported_tag("v2.3")
    assert not self_update.is_valid_selector_tag("1.0")
    assert not self_update.is_valid_selector_tag("v1")
    assert not self_update.is_valid_selector_tag("v1.0.0")
    assert not self_update.is_valid_selector_tag("v1.0.0.1")
    assert not self_update._is_selector_supported_tag("v0.9")
    assert not self_update._is_selector_supported_tag("v0.99")


def test_self_update_selector_tags_are_sorted_numerically():
    assert self_update._sort_selector_supported_tags(["v1.9", "v2.0", "v1.10"]) == [
        "v2.0",
        "v1.10",
        "v1.9",
    ]


def test_self_update_branch_filter_prefers_remote_branch_tags(monkeypatch):
    monkeypatch.setattr(
        self_update.git,
        "get_remote_releases",
        lambda author, repo: types.SimpleNamespace(
            error="",
            releases=[
                types.SimpleNamespace(tag="v1.2"),
                types.SimpleNamespace(tag="v1.1"),
                types.SimpleNamespace(tag="v1.0"),
            ],
        ),
    )
    monkeypatch.setattr(
        self_update,
        "_get_remote_branch_merged_tags",
        lambda branch: {"v1.1", "v1.0"},
    )
    monkeypatch.setattr(
        self_update,
        "_get_local_branch_merged_tags",
        lambda branch, repo_dir=None: set(),
    )

    tags, error = self_update.get_available_tags("development")

    assert error == ""
    assert tags == ["v1.1", "v1.0"]


def test_self_update_frontend_filters_old_tag_suggestions():
    store_path = (
        PROJECT_ROOT
        / "webui"
        / "components"
        / "settings"
        / "external"
        / "self-update-store.js"
    )
    content = store_path.read_text(encoding="utf-8")

    assert "const MIN_SELECTOR_VERSION = [1, 0];" in content
    assert "response.tags.filter((tag) => this.isSupportedSuggestionTag(tag))" in content
    assert "Release tag must use the format vX.Y." in content
    assert "Release tag must be v1.0 or newer." in content
    assert "this.info?.defaults?.branch ||" in content
    assert "Version ${tag} does not exist on branch" in content
    assert "this.selectedTagExistsOnBranch" in content
    assert 'const response = await fetch("/api/health"' in content
    assert "if (response.ok && observedBackendUnavailable)" in content
    assert "Waiting for Agent Zero to disconnect before reloading the page." in content
    assert "/api/csrf_token" not in content


def test_self_update_modal_validates_exact_tag_on_blur():
    modal_path = (
        PROJECT_ROOT
        / "webui"
        / "components"
        / "settings"
        / "external"
        / "self-update-modal.html"
    )
    content = modal_path.read_text(encoding="utf-8")

    assert '@blur="$store.selfUpdateStore.onTagBlur()"' in content
    assert '@mousedown.prevent="$store.selfUpdateStore.selectTag(tag)"' in content
    assert "$store.selfUpdateStore.tagExistenceWarning" in content
    assert 'type="button"' in content


def test_self_update_schedule_rejects_missing_tag_on_branch(monkeypatch, tmp_path):
    monkeypatch.setattr(
        self_update,
        "get_repo_version_info",
        lambda _repo: {
            "branch": "development",
            "describe": "v1.0",
            "short_tag": "v1.0",
            "commit": "abc123",
            "short_commit": "abc123",
        },
    )
    monkeypatch.setattr(
        self_update,
        "get_available_tags",
        lambda branch, *, repo_dir=None, query="": (["v1.0"], ""),
    )
    monkeypatch.setattr(self_update, "_write_yaml", lambda path, payload: None)

    with pytest.raises(ValueError, match=r"Version v1\.1 does not exist on branch development\."):
        self_update.schedule_update(
            branch="development",
            tag="v1.1",
            backup_usr=True,
            backup_path="",
            backup_name="",
            backup_conflict_policy="rename",
            repo_dir=tmp_path,
        )
