import importlib.util
import socket
import sys
import tempfile
import types
import zipfile
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

sys.modules["giturlparse"] = types.SimpleNamespace(parse=lambda *args, **kwargs: None)

from helpers import self_update


def load_self_update_manager():
    manager_path = (
        PROJECT_ROOT / "docker" / "run" / "fs" / "exe" / "self_update_manager.py"
    )
    spec = importlib.util.spec_from_file_location("test_self_update_manager", manager_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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


def test_self_update_available_branch_values_filter_prs_and_pin_main_first(monkeypatch):
    monkeypatch.setattr(self_update, "_remote_branch_list_cache", None)
    monkeypatch.setattr(
        self_update,
        "_run_git_raw",
        lambda *args: "\n".join(
            [
                "111 refs/heads/testing",
                "222 refs/heads/ready",
                "333 refs/heads/pr/123",
                "444 refs/heads/development",
                "555 refs/heads/main",
                "666 refs/heads/pr-999",
            ]
        ),
    )

    branches = self_update.get_available_branch_values()

    assert branches == ["main", "development", "ready", "testing"]


def test_self_update_available_branch_values_fallback_to_local_origin(monkeypatch):
    monkeypatch.setattr(self_update, "_remote_branch_list_cache", None)
    monkeypatch.setattr(
        self_update,
        "_run_git_raw",
        lambda *args: (_ for _ in ()).throw(RuntimeError("offline")),
    )
    monkeypatch.setattr(
        self_update,
        "_run_git",
        lambda repo_dir, *args: "\n".join(
            [
                "origin/HEAD",
                "origin/ready",
                "origin/testing",
                "origin/pr/999",
                "origin/main",
            ]
        ),
    )

    branches = self_update.get_available_branch_values()

    assert branches == ["main", "ready", "testing"]


def test_self_update_uses_durable_manager_capability_when_present(monkeypatch, tmp_path):
    durable_manager = tmp_path / "self_update_manager.py"
    repo_manager = tmp_path / "repo-self_update_manager.py"
    durable_manager.write_text("# old manager without latest\n", encoding="utf-8")
    repo_manager.write_text(
        'LATEST_SELECTOR_TAG = "latest"\n'
        "def resolve_requested_target():\n"
        "    pass\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        self_update,
        "get_durable_self_update_manager_path",
        lambda: durable_manager,
    )
    monkeypatch.setattr(
        self_update,
        "get_repo_self_update_manager_path",
        lambda repo_dir=None: repo_manager,
    )

    assert self_update.durable_self_update_supports_latest() is False


def test_self_update_falls_back_to_repo_manager_capability_when_durable_missing(monkeypatch, tmp_path):
    missing_durable = tmp_path / "missing-self_update_manager.py"
    repo_manager = tmp_path / "repo-self_update_manager.py"
    repo_manager.write_text(
        'LATEST_SELECTOR_TAG = "latest"\n'
        "def resolve_requested_target():\n"
        "    pass\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        self_update,
        "get_durable_self_update_manager_path",
        lambda: missing_durable,
    )
    monkeypatch.setattr(
        self_update,
        "get_repo_self_update_manager_path",
        lambda repo_dir=None: repo_manager,
    )

    assert self_update.durable_self_update_supports_latest() is True


def test_self_update_selector_tag_options_filter_to_current_major(monkeypatch):
    monkeypatch.setattr(
        self_update,
        "get_available_tags",
        lambda branch, *, repo_dir=None, query="": (
            ["v3.0", "v2.1", "v1.4", "v1.2"],
            "",
        ),
    )
    monkeypatch.setattr(
        self_update,
        "_get_branch_head_info",
        lambda branch, repo_dir=None: {
            "describe": "v1.4-4-gabc1234",
            "short_tag": "v1.4",
            "commit": "abc1234",
        },
    )
    monkeypatch.setattr(
        self_update,
        "durable_self_update_supports_latest",
        lambda repo_dir=None: True,
    )

    tag_options, higher_major_versions, error = self_update.get_selector_tag_options(
        "main",
        current_version="v1.2",
    )

    assert error == ""
    assert tag_options == [
        {"value": "latest", "label": "latest (v1.4)"},
        {"value": "v1.4", "label": "v1.4"},
        {"value": "v1.2", "label": "v1.2"},
    ]
    assert higher_major_versions == [2, 3]


def test_self_update_selector_tag_options_keep_main_latest_within_current_major(monkeypatch):
    monkeypatch.setattr(
        self_update,
        "get_available_tags",
        lambda branch, *, repo_dir=None, query="": (
            ["v2.0", "v1.4", "v1.2"],
            "",
        ),
    )
    monkeypatch.setattr(
        self_update,
        "_get_branch_head_info",
        lambda branch, repo_dir=None: {
            "describe": "v2.0",
            "short_tag": "v2.0",
            "commit": "def5678",
        },
    )
    monkeypatch.setattr(
        self_update,
        "durable_self_update_supports_latest",
        lambda repo_dir=None: True,
    )

    tag_options, higher_major_versions, error = self_update.get_selector_tag_options(
        "main",
        current_version="v1.2",
    )

    assert error == ""
    assert tag_options == [
        {"value": "latest", "label": "latest (v1.4)"},
        {"value": "v1.4", "label": "v1.4"},
        {"value": "v1.2", "label": "v1.2"},
    ]
    assert higher_major_versions == [2]


def test_self_update_selector_tag_options_hide_latest_when_durable_updater_lacks_support(monkeypatch):
    monkeypatch.setattr(
        self_update,
        "get_available_tags",
        lambda branch, *, repo_dir=None, query="": (
            ["v1.4", "v1.2"],
            "",
        ),
    )
    monkeypatch.setattr(
        self_update,
        "_get_branch_head_info",
        lambda branch, repo_dir=None: {
            "describe": "v1.4-4-gabc1234",
            "short_tag": "v1.4",
            "commit": "abc1234",
        },
    )
    monkeypatch.setattr(
        self_update,
        "durable_self_update_supports_latest",
        lambda repo_dir=None: False,
    )

    tag_options, higher_major_versions, error = self_update.get_selector_tag_options(
        "development",
        current_version="v1.2",
    )

    assert error == ""
    assert tag_options == [
        {"value": "v1.4", "label": "v1.4"},
        {"value": "v1.2", "label": "v1.2"},
    ]
    assert higher_major_versions == []


def test_self_update_update_info_uses_current_branch_for_latest_version(monkeypatch):
    monkeypatch.setattr(
        self_update,
        "get_repo_version_info",
        lambda _repo=None: {
            "branch": "main",
            "describe": "v1.2",
            "short_tag": "v1.2",
            "display_version": "v1.2",
            "commit": "abc1234def",
            "short_commit": "abc1234",
        },
    )
    monkeypatch.setattr(
        self_update,
        "get_available_branches",
        lambda repo_dir=None: [
            {"value": "main", "label": "main"},
            {"value": "ready", "label": "ready"},
            {"value": "testing", "label": "testing"},
        ],
    )
    monkeypatch.setattr(
        self_update,
        "get_available_branch_values",
        lambda repo_dir=None: ["main", "ready", "testing"],
    )
    monkeypatch.setattr(
        self_update,
        "get_selector_tag_options",
        lambda branch, *, repo_dir=None, current_version=None: (
            [{"value": "latest", "label": "latest (v1.4)"}],
            [2] if branch == "main" else [],
            "",
        ),
    )
    monkeypatch.setattr(
        self_update,
        "get_available_tags",
        lambda branch, *, repo_dir=None, query="": (["v1.4", "v1.2"], ""),
    )
    monkeypatch.setattr(
        self_update,
        "durable_self_update_supports_latest",
        lambda repo_dir=None: True,
    )
    monkeypatch.setattr(self_update, "load_pending_update", lambda: None)
    monkeypatch.setattr(self_update, "load_last_status", lambda: None)
    monkeypatch.setattr(
        self_update,
        "_get_branch_head_info",
        lambda branch, repo_dir=None: {
            "main": {
                "describe": "v1.4",
                "short_tag": "v1.4",
                "commit": "def5678abcd",
            },
            "development": {
                "describe": "v9.9-3-gfeedbee",
                "short_tag": "v9.9",
                "commit": "feedbee1234",
            },
        }[branch],
    )

    info = self_update.get_update_info()

    assert info["current_branch_latest"] == {
        "branch": "main",
        "supported": True,
        "describe": "v1.4",
        "short_tag": "v1.4",
        "display_version": "v1.4",
        "commit": "def5678abcd",
        "short_commit": "def5678",
        "released_at": "",
    }
    assert info["main_branch_latest"] == {
        "branch": "main",
        "supported": True,
        "describe": "v1.4",
        "short_tag": "v1.4",
        "display_version": "v1.4",
        "commit": "def5678abcd",
        "short_commit": "def5678",
        "released_at": "",
    }
    assert info["major_upgrade_versions"] == [2]


def test_self_update_main_branch_latest_stays_within_current_major(monkeypatch, tmp_path):
    monkeypatch.setattr(
        self_update,
        "get_available_branch_values",
        lambda repo_dir=None: ["main", "development"],
    )
    monkeypatch.setattr(
        self_update,
        "get_available_tags",
        lambda branch, *, repo_dir=None, query="": (
            ["v2.0", "v1.4", "v1.2"],
            "",
        ),
    )
    monkeypatch.setattr(
        self_update,
        "_get_branch_head_info",
        lambda branch, repo_dir=None: {
            "describe": "v2.0",
            "short_tag": "v2.0",
            "commit": "feedbee1234",
            "released_at": "2026-03-30 15:15:50",
        },
    )
    monkeypatch.setattr(
        self_update,
        "_run_git",
        lambda repo_dir, *args: {
            ("rev-parse", "refs/tags/v1.4^{commit}"): "deadbeef1234",
        }[args],
    )
    monkeypatch.setattr(
        self_update,
        "_get_tag_release_time_in_repo",
        lambda repo_dir, tag: "2026-02-01 08:30:00" if tag == "v1.4" else "",
    )

    info = self_update.get_current_major_main_latest_info("v1.2", repo_dir=tmp_path)

    assert info == {
        "branch": "main",
        "supported": True,
        "describe": "v1.4",
        "short_tag": "v1.4",
        "display_version": "v1.4",
        "commit": "deadbeef1234",
        "short_commit": "deadbee",
        "released_at": "2026-02-01 08:30:00",
    }


def test_self_update_remote_branch_head_info_resolves_release_time_before_temp_repo_is_removed(
    monkeypatch,
):
    monkeypatch.setattr(self_update, "_remote_branch_head_cache", {})

    def fake_run_git(repo_dir, *args):
        if args[:2] == ("init", "--bare"):
            return ""
        if args[0] == "fetch":
            return ""
        if args[:3] == ("describe", "--tags", "--always"):
            return "v1.5"
        if args[:2] == ("rev-parse", "refs/remotes/origin/main"):
            return "abc1234def5678"
        raise AssertionError(args)

    monkeypatch.setattr(self_update, "_run_git", fake_run_git)
    monkeypatch.setattr(
        self_update,
        "_get_tag_release_time_in_repo",
        lambda repo_dir, tag: "2026-03-30 15:15:50" if Path(repo_dir).exists() else "",
    )

    info = self_update._get_remote_branch_head_info("main")

    assert info == {
        "describe": "v1.5",
        "short_tag": "v1.5",
        "commit": "abc1234def5678",
        "released_at": "2026-03-30 15:15:50",
    }


def test_self_update_frontend_uses_preloaded_select():
    store_path = (
        PROJECT_ROOT
        / "webui"
        / "components"
        / "settings"
        / "external"
        / "self-update-store.js"
    )
    content = store_path.read_text(encoding="utf-8")

    assert 'const SELF_UPDATE_MANUAL_BACKUP_MODAL_PATH = "settings/backup/backup_restore.html";' in content
    assert "const MIN_SELECTOR_VERSION = [1, 0];" in content
    assert "availableTagOptions: []" in content
    assert "higherMajorVersions: []" in content
    assert "majorUpgradeVersions: []" in content
    assert 'activeTab: "quick"' in content
    assert "get hasPendingInitialLoad()" in content
    assert "get isCheckingStatus()" in content
    assert "get hasMajorUpgrade()" in content
    assert "get majorUpgradeBannerMessage()" in content
    assert "this.applyAvailableTags({" in content
    assert "response.available_tag_options" in content
    assert "response.available_higher_major_versions" in content
    assert "response.major_upgrade_versions" in content
    assert "response.tag_options" in content
    assert "response.higher_major_versions" in content
    assert "response.pending || {" in content
    assert "tag: \"\"," in content
    assert "await this.fetchTags();" in content
    assert '"Preparing update"' in content
    assert '"Saving the request and asking Agent Zero to restart."' in content
    assert "Release tag must use the format vX.Y." in content
    assert "Release tag must be v1.0 or newer." in content
    assert "isLatestSelectorTag(value)" in content
    assert "this.isSelectableTag(this.form.tag)" in content
    assert "get mainBranchLatestTag()" in content
    assert "quickUpdateAvailable" in content
    assert "scheduleQuickUpdate()" in content
    assert 'branch: "main"' in content
    assert "quickComparisonIcon" in content
    assert "quickComparisonIconClass" in content
    assert "Checking update status..." in content
    assert '"CHECKING"' in content
    assert '"Loading"' in content
    assert "formatReleaseTimestamp(value)" in content
    assert "getLastStatusBadgeClass(status)" in content
    assert "this.info?.current?.display_version" in content
    assert "this.info?.main_branch_latest?.display_version" in content
    assert "this.info?.current?.released_at" in content
    assert "resetRestartState()" in content
    assert "restartRequestStarted" in content
    assert "restartResponse.status >= 500" in content
    assert "while Agent Zero was shutting down" in content
    assert "await notificationStore.frontendWarning(" not in content
    assert "status-pill-error" in content
    assert "status-pill-success" in content
    assert "this.info?.defaults?.branch ||" in content
    assert "Version ${this.trimmedTag} does not exist on branch" in content
    assert "this.selectedTagExistsOnBranch" in content
    assert "this.form.tag = \"\";" in content
    assert "this.availableTags[0]" not in content
    assert 'const response = await fetch("/api/health"' in content
    assert "if (response.ok && observedBackendUnavailable)" in content
    assert "window.location.reload();" in content
    assert "Waiting for Agent Zero to disconnect before reloading the page." in content
    assert "SELF_UPDATE_RETURN_URL_KEY" not in content
    assert "saveReturnUrl(" not in content
    assert "getSavedReturnUrl(" not in content
    assert "/api/csrf_token" not in content
    assert "tagSuggestions" not in content
    assert "tagDropdownOpen" not in content


def test_self_update_modal_uses_standard_select_and_manual_backup():
    modal_path = (
        PROJECT_ROOT
        / "webui"
        / "components"
        / "settings"
        / "external"
        / "self-update-modal.html"
    )
    content = modal_path.read_text(encoding="utf-8")

    assert 'x-model="$store.selfUpdateStore.form.tag"' in content
    assert "$store.selfUpdateStore.versionSelectPlaceholder" in content
    assert "$store.selfUpdateStore.higherMajorVersionMessage" in content
    assert "$store.selfUpdateStore.availableTagOptions" in content
    assert "$store.selfUpdateStore.info?.current?.describe" in content
    assert "current_branch_latest?.display_version" in content
    assert "mainBranchLatestVersion" in content
    assert "tagOption.label" in content
    assert 'id="self-update-quick-tab"' in content
    assert 'id="self-update-advanced-tab"' in content
    assert 'data-bs-target="#self-update-last-attempt-collapse"' in content
    assert "New major version available" in content
    assert 'x-show="$store.selfUpdateStore.hasMajorUpgrade"' in content
    assert "$store.selfUpdateStore.majorUpgradeBannerMessage" in content
    assert "Website installation guide" in content
    assert "self-update-header-status" in content
    assert ".status-pill.self-update-quick-status" in content
    assert "getLastStatusLabel($store.selfUpdateStore.info?.last_status?.status)" in content
    assert "Current version vs latest on main" not in content
    assert "quickComparisonIcon" in content
    assert "quickComparisonIconClass" in content
    assert "{ spinning: $store.selfUpdateStore.isCheckingStatus }" in content
    assert "{ 'btn-field': !$store.selfUpdateStore.quickUpdateAvailable }" in content
    assert "{ 'btn-field': !$store.selfUpdateStore.canScheduleUpdate }" in content
    assert "formatReleaseTimestamp($store.selfUpdateStore.currentReleasedAt)" in content
    assert "formatReleaseTimestamp($store.selfUpdateStore.mainBranchLatestReleasedAt)" in content
    assert "Latest version" in content
    assert "Docker update guide" in content
    assert "https://www.agent-zero.ai/p/docs/get-started/" in content
    assert "Version numbers use the format <code>vMAJOR.MINOR</code>" in content
    assert "requires a newer" in content
    assert "Docker image." in content
    assert "minor release line" in content
    assert "Agent Zero self-update inside the existing image." in content
    assert "On development branches you may also see versions like <code>v1.5+2</code>" in content
    assert "This suffix is not used on" in content
    assert "Only versions from the current major release line are listed here." in content
    assert "Manual backup" in content
    assert ">Refresh Status<" not in content
    assert "Refresh" in content
    assert "Loading update status..." not in content
    assert 'type="button"' in content
    assert "@blur" not in content
    assert "selectTag(tag)" not in content


def test_self_update_repo_version_info_includes_display_version_for_non_main(monkeypatch, tmp_path):
    monkeypatch.setattr(
        self_update,
        "_run_git",
        lambda repo_dir, *args: {
            ("describe", "--tags", "--always"): "v1.11-9-gf69147a",
            ("rev-parse", "HEAD"): "f69147a123456789",
            ("branch", "--show-current"): "development",
        }[args],
    )

    info = self_update.get_repo_version_info(tmp_path)

    assert info["short_tag"] == "v1.11"
    assert info["display_version"] == "v1.11+9"
    assert info["short_commit"] == "f69147a"


def test_self_update_recovery_script_and_docs_are_present():
    script_path = PROJECT_ROOT / "docker" / "run" / "fs" / "exe" / "trigger_self_update.sh"
    script_content = script_path.read_text(encoding="utf-8")
    docs_path = PROJECT_ROOT / "docs" / "guides" / "troubleshooting.md"
    docs_content = docs_path.read_text(encoding="utf-8")
    dockerfile_path = PROJECT_ROOT / "docker" / "run" / "Dockerfile"
    dockerfile_content = dockerfile_path.read_text(encoding="utf-8")

    assert 'trigger-update "$@"' in script_content
    assert "/exe/trigger_self_update.sh" in docs_content
    assert "docker exec -it <container>" in docs_content
    assert "/exe/a0-self-update.log" in docs_content
    assert "reload the current browser window" in docs_content
    assert "main` and `latest`" in docs_content
    assert "/exe/trigger_self_update.sh" in dockerfile_content


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
        "get_selector_tag_options",
        lambda branch, *, repo_dir=None, current_version=None: (
            [{"value": "v1.0", "label": "v1.0"}],
            [],
            "",
        ),
    )
    monkeypatch.setattr(
        self_update,
        "get_available_branch_values",
        lambda repo_dir=None: ["development", "ready", "testing", "main"],
    )
    monkeypatch.setattr(
        self_update,
        "durable_self_update_supports_latest",
        lambda repo_dir=None: True,
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


def test_self_update_schedule_accepts_latest_when_selector_exposes_it(monkeypatch, tmp_path):
    monkeypatch.setattr(
        self_update,
        "get_repo_version_info",
        lambda _repo: {
            "branch": "development",
            "describe": "v1.4-2-gabc1234",
            "short_tag": "v1.4",
            "commit": "abc1234",
            "short_commit": "abc1234",
        },
    )
    captured_payload = {}
    monkeypatch.setattr(
        self_update,
        "get_selector_tag_options",
        lambda branch, *, repo_dir=None, current_version=None: (
            [{"value": "latest", "label": "latest (v1.4+2)"}],
            [],
            "",
        ),
    )
    monkeypatch.setattr(
        self_update,
        "get_available_branch_values",
        lambda repo_dir=None: ["development", "ready", "testing", "main"],
    )
    monkeypatch.setattr(
        self_update,
        "durable_self_update_supports_latest",
        lambda repo_dir=None: True,
    )
    monkeypatch.setattr(
        self_update,
        "_write_yaml",
        lambda path, payload: captured_payload.update(payload),
    )

    payload = self_update.schedule_update(
        branch="development",
        tag="latest",
        backup_usr=True,
        backup_path="",
        backup_name="",
        backup_conflict_policy="rename",
        repo_dir=tmp_path,
    )

    assert payload["tag"] == "latest"
    assert captured_payload["tag"] == "latest"


def test_self_update_manager_queues_update_with_main_latest_defaults(monkeypatch):
    manager = load_self_update_manager()
    captured = {}
    monkeypatch.setattr(
        manager,
        "get_repo_version_info",
        lambda _repo: {
            "branch": "main",
            "describe": "v1.2",
            "short_tag": "v1.2",
            "commit": "abc1234",
        },
    )
    monkeypatch.setattr(
        manager,
        "write_yaml",
        lambda path, payload: captured.update({"path": path, "payload": payload}),
    )

    payload = manager.queue_update_request(branch="", tag="")

    assert payload["branch"] == "main"
    assert payload["tag"] == "latest"
    assert payload["backup_usr"] is True
    assert payload["backup_path"] == "/root/update-backups"
    assert payload["backup_conflict_policy"] == "rename"
    assert captured["path"] == manager.TRIGGER_FILE
    assert captured["payload"]["tag"] == "latest"


def test_self_update_manager_usr_backup_skips_broken_symlinks(tmp_path):
    manager = load_self_update_manager()
    repo_dir = tmp_path / "repo"
    usr_dir = repo_dir / "usr"
    venv_bin = usr_dir / "workdir" / "reachy-mini-mcp" / ".venv" / "bin"
    venv_bin.mkdir(parents=True)
    (usr_dir / "settings.json").write_text('{"ok": true}\n', encoding="utf-8")
    broken_symlink = venv_bin / "python"
    broken_symlink.symlink_to("/missing/host/python")

    backup_path = manager.create_usr_backup(
        repo_dir=repo_dir,
        backup_path=str(tmp_path / "backups"),
        backup_name="usr-backup.zip",
        conflict_policy="rename",
        logger=manager.NullLogger(),
    )

    with zipfile.ZipFile(backup_path) as archive:
        names = set(archive.namelist())

    assert "usr/settings.json" in names
    assert "usr/workdir/reachy-mini-mcp/.venv/bin/python" not in names


def test_self_update_manager_usr_backup_skips_runtime_sockets():
    manager = load_self_update_manager()
    with tempfile.TemporaryDirectory(prefix="a0su-", dir="/tmp") as temp_root:
        repo_dir = Path(temp_root) / "repo"
        usr_dir = repo_dir / "usr"
        gnupg_dir = (
            usr_dir
            / "plugins"
            / "_desktop"
            / "profiles"
            / "agent-zero-desktop"
            / ".gnupg"
        )
        gnupg_dir.mkdir(parents=True)
        (usr_dir / "settings.json").write_text('{"ok": true}\n', encoding="utf-8")
        socket_path = gnupg_dir / "S.gpg-agent"
        messages = []

        class ListLogger:
            def log(self, message=""):
                messages.append(message)

        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as runtime_socket:
            runtime_socket.bind(str(socket_path))
            backup_path = manager.create_usr_backup(
                repo_dir=repo_dir,
                backup_path=str(Path(temp_root) / "backups"),
                backup_name="usr-backup.zip",
                conflict_policy="rename",
                logger=ListLogger(),
            )

        with zipfile.ZipFile(backup_path) as archive:
            names = set(archive.namelist())

        assert "usr/settings.json" in names
        assert (
            "usr/plugins/_desktop/profiles/agent-zero-desktop/.gnupg/S.gpg-agent"
            not in names
        )
        assert any(
            "Skipping non-regular usr backup entry" in message
            for message in messages
        )


def test_self_update_manager_clean_uv_cache_uses_uv_when_available(monkeypatch):
    manager = load_self_update_manager()
    commands = []
    monkeypatch.setattr(
        manager.shutil,
        "which",
        lambda executable: "/usr/local/bin/uv" if executable == "uv" else None,
    )

    def fake_run_command(command, *, cwd, logger, error_message=None):
        commands.append((command, cwd, error_message))

    monkeypatch.setattr(manager, "run_command", fake_run_command)

    manager.clean_uv_cache(manager.NullLogger())

    assert commands == [
        (
            ["/usr/local/bin/uv", "cache", "clean"],
            None,
            "Failed to clean uv cache during self-update.",
        )
    ]


def test_self_update_manager_clean_uv_cache_skips_when_uv_missing(monkeypatch):
    manager = load_self_update_manager()
    commands = []
    monkeypatch.setattr(manager.shutil, "which", lambda executable: None)
    monkeypatch.setattr(
        manager,
        "run_command",
        lambda command, **kwargs: commands.append(command),
    )

    manager.clean_uv_cache(manager.NullLogger())

    assert commands == []


def test_self_update_manager_clean_uv_cache_is_best_effort(monkeypatch):
    manager = load_self_update_manager()
    messages = []
    monkeypatch.setattr(
        manager.shutil,
        "which",
        lambda executable: "/usr/local/bin/uv" if executable == "uv" else None,
    )

    class Logger:
        def log(self, message=""):
            messages.append(message)

        def log_block(self, title, content):
            return None

    def fail_run_command(command, **kwargs):
        raise RuntimeError("cache cleanup failed")

    monkeypatch.setattr(manager, "run_command", fail_run_command)

    manager.clean_uv_cache(Logger())

    assert any("uv cache clean skipped after error" in message for message in messages)


def test_self_update_manager_latest_on_main_uses_current_major_release(monkeypatch):
    manager = load_self_update_manager()
    monkeypatch.setattr(
        manager,
        "fetch_branch_refs",
        lambda repo_dir, branch, logger: "refs/remotes/a0-self-update/main",
    )
    monkeypatch.setattr(
        manager,
        "git_output",
        lambda repo_dir, *args: {
            ("tag", "--merged", "refs/remotes/a0-self-update/main"): "v2.0\nv1.4\nv1.2\n",
            ("rev-parse", "refs/tags/v1.4^{commit}"): "deadbeef1234",
        }[args],
    )

    resolved = manager.resolve_requested_target(
        Path("/tmp/repo"),
        "main",
        "latest",
        "v1.2",
        manager.NullLogger(),
    )

    assert resolved["effective_tag"] == "v1.4"
    assert resolved["expected_short_tag"] == "v1.4"
    assert resolved["expected_commit"] == "deadbeef1234"


def test_self_update_manager_explicit_tag_uses_peeled_commit(monkeypatch):
    manager = load_self_update_manager()
    monkeypatch.setattr(manager, "fetch_release_refs", lambda repo_dir, branch, tag, logger: None)
    monkeypatch.setattr(
        manager,
        "git_output",
        lambda repo_dir, *args: {
            ("rev-parse", "refs/tags/v1.10^{commit}"): "192d6e2cae1a85c0a2e7a6ecf41c153b39f1b4c6",
        }[args],
    )

    resolved = manager.resolve_requested_target(
        Path("/tmp/repo"),
        "development",
        "v1.10",
        "v1.11",
        manager.NullLogger(),
    )

    assert resolved["effective_tag"] == "v1.10"
    assert resolved["expected_commit"] == "192d6e2cae1a85c0a2e7a6ecf41c153b39f1b4c6"


def test_self_update_manager_skip_check_requires_exact_describe_match():
    manager = load_self_update_manager()

    assert (
        manager.installed_target_matches_request(
            {
                "branch": "development",
                "describe": "v1.11",
                "short_tag": "v1.11",
            },
            requested_branch="development",
            requested_tag="v1.11",
        )
        is True
    )
    assert (
        manager.installed_target_matches_request(
            {
                "branch": "development",
                "describe": "v1.11-12-ge9d9c93d",
                "short_tag": "v1.11",
            },
            requested_branch="development",
            requested_tag="v1.11",
        )
        is False
    )
    assert (
        manager.installed_target_matches_request(
            {
                "branch": "development",
                "describe": "v1.11",
                "short_tag": "v1.11",
            },
            requested_branch="development",
            requested_tag="latest",
        )
        is False
    )


def test_self_update_manager_fetch_release_refs_checks_peeled_tag_commit(monkeypatch):
    manager = load_self_update_manager()
    commands = []
    monkeypatch.setattr(
        manager,
        "run_command",
        lambda command, **kwargs: commands.append(command),
    )

    manager.fetch_release_refs(
        Path("/tmp/repo"),
        "development",
        "v1.10",
        manager.NullLogger(),
    )

    assert commands[1][-2] == "refs/tags/v1.10^{commit}"


def test_self_update_manager_latest_on_non_main_rejects_cross_major(monkeypatch):
    manager = load_self_update_manager()
    monkeypatch.setattr(
        manager,
        "fetch_branch_refs",
        lambda repo_dir, branch, logger: "refs/remotes/a0-self-update/development",
    )
    monkeypatch.setattr(
        manager,
        "git_output",
        lambda repo_dir, *args: {
            ("describe", "--tags", "--always", "refs/remotes/a0-self-update/development"): "v2.0-3-gabc1234",
            ("rev-parse", "refs/remotes/a0-self-update/development"): "abc123456789",
        }[args],
    )

    with pytest.raises(RuntimeError, match=r"Use an explicit tag to change major versions"):
        manager.resolve_requested_target(
            Path("/tmp/repo"),
            "development",
            "latest",
            "v1.2",
            manager.NullLogger(),
        )


def test_self_update_schedule_rejects_latest_when_durable_updater_lacks_support(monkeypatch, tmp_path):
    monkeypatch.setattr(
        self_update,
        "get_repo_version_info",
        lambda _repo: {
            "branch": "development",
            "describe": "v1.4-2-gabc1234",
            "short_tag": "v1.4",
            "commit": "abc1234",
            "short_commit": "abc1234",
        },
    )
    monkeypatch.setattr(
        self_update,
        "get_available_branch_values",
        lambda repo_dir=None: ["development", "ready", "testing", "main"],
    )
    monkeypatch.setattr(
        self_update,
        "durable_self_update_supports_latest",
        lambda repo_dir=None: False,
    )

    with pytest.raises(
        ValueError,
        match=r"durable updater does not support the latest selector",
    ):
        self_update.schedule_update(
            branch="development",
            tag="latest",
            backup_usr=True,
            backup_path="",
            backup_name="",
            backup_conflict_policy="rename",
            repo_dir=tmp_path,
        )
