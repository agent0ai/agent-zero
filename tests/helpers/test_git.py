"""Tests for python/helpers/git.py — strip_auth_from_url, get_version, clone_repo, get_repo_status."""

import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.helpers import git


class TestStripAuthFromUrl:
    def test_removes_user_from_url(self):
        url = "https://user:pass@github.com/org/repo.git"
        assert "user" not in git.strip_auth_from_url(url)
        assert "pass" not in git.strip_auth_from_url(url)
        assert "github.com" in git.strip_auth_from_url(url)

    def test_preserves_url_without_auth(self):
        url = "https://github.com/org/repo.git"
        assert git.strip_auth_from_url(url) == url

    def test_handles_empty_url(self):
        assert git.strip_auth_from_url("") == ""

    def test_preserves_port(self):
        url = "https://user:pass@host.example.com:8080/path"
        result = git.strip_auth_from_url(url)
        assert ":8080" in result
        assert "user" not in result


class TestGetVersion:
    def test_returns_version_from_git_info(self):
        with patch("python.helpers.git.get_git_info") as m:
            m.return_value = {"short_tag": "v0.9.8", "branch": "main"}
            assert git.get_version() == "v0.9.8"

    def test_falls_back_to_env(self):
        with patch("python.helpers.git.get_git_info", side_effect=Exception("no git")):
            with patch.dict(os.environ, {"A0_VERSION": "v1.0.0"}, clear=False):
                assert git.get_version() == "v1.0.0"

    def test_falls_back_to_version_file(self, tmp_path):
        version_file = tmp_path / "VERSION"
        version_file.write_text("v0.9.9")
        with patch("python.helpers.git.get_git_info", side_effect=Exception("no git")):
            with patch.dict(os.environ, {}, clear=True):
                with patch("python.helpers.git.files") as mf:
                    mf.get_base_dir.return_value = str(tmp_path)
                    assert git.get_version() == "v0.9.9"

    def test_returns_unknown_when_all_fail(self):
        with patch("python.helpers.git.get_git_info", side_effect=Exception("no git")):
            with patch.dict(os.environ, {}, clear=True):
                with patch("python.helpers.git.files") as mf:
                    mf.get_base_dir.return_value = "/tmp"
                    with patch("os.path.isfile", return_value=False):
                        assert git.get_version() == "unknown"


class TestCloneRepo:
    def test_clone_without_token(self):
        with patch("subprocess.run") as m:
            m.return_value = MagicMock(returncode=0)
            with patch("python.helpers.git.Repo") as mr:
                git.clone_repo("https://github.com/org/repo", "/tmp/dest")
        m.assert_called_once()
        args = m.call_args[0][0]
        assert "clone" in args
        assert "https://github.com/org/repo" in args
        assert "/tmp/dest" in args

    def test_clone_with_token_adds_extra_header(self):
        with patch("subprocess.run") as m:
            m.return_value = MagicMock(returncode=0)
            with patch("python.helpers.git.Repo"):
                git.clone_repo("https://github.com/org/repo", "/tmp/dest", token="ghp_xxx")
        args = m.call_args[0][0]
        assert "-c" in args
        assert "http.extraHeader" in str(args)
        assert "Authorization" in str(args)

    def test_clone_raises_on_failure(self):
        with patch("subprocess.run") as m:
            m.return_value = MagicMock(returncode=1, stderr="fatal: error", stdout="")
            with pytest.raises(Exception) as exc:
                git.clone_repo("https://x.com/r", "/tmp/d")
        assert "Git clone failed" in str(exc.value)


class TestGetRepoStatus:
    def test_returns_not_git_repo_on_error(self):
        with patch("python.helpers.git.Repo", side_effect=Exception("not a repo")):
            result = git.get_repo_status("/tmp")
        assert result["is_git_repo"] is False
        assert "error" in result

    def test_returns_status_for_valid_repo(self):
        mock_repo = MagicMock()
        mock_repo.bare = False
        mock_repo.remotes.origin.url = "https://github.com/org/repo"
        mock_repo.active_branch.name = "main"
        mock_repo.head.is_detached = False
        mock_repo.index.diff.return_value = []
        mock_repo.untracked_files = []
        mock_repo.head.commit.hexsha = "abc1234"
        mock_repo.head.commit.message = "test commit"
        mock_repo.head.commit.author = "Author"
        mock_repo.head.commit.committed_date = 1234567890

        with patch("python.helpers.git.Repo", return_value=mock_repo):
            result = git.get_repo_status("/tmp/repo")
        assert result["is_git_repo"] is True
        assert result["current_branch"] == "main"
        assert "remote_url" in result or "remote" in str(result).lower()
