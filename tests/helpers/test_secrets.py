"""Tests for python/helpers/secrets.py — secret masking/unmasking/storage."""

import re
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# --- Fixtures ---


@pytest.fixture(autouse=True)
def _reset_secrets_manager():
    """Reset SecretsManager class-level state before each test."""
    from python.helpers import secrets as secrets_module

    orig_instances = secrets_module.SecretsManager._instances.copy()
    secrets_module.SecretsManager._instances.clear()
    yield
    secrets_module.SecretsManager._instances.clear()
    secrets_module.SecretsManager._instances.update(orig_instances)


@pytest.fixture
def mock_files(tmp_path):
    """Mock files helper for read/write operations."""
    with patch("python.helpers.secrets.files") as m:
        m.read_file.side_effect = lambda p: ""
        m.write_file.side_effect = lambda p, c: None
        yield m


# --- alias_for_key ---


class TestAliasForKey:
    def test_uppercases_key(self):
        from python.helpers.secrets import alias_for_key

        assert alias_for_key("api_key") == "§§secret(API_KEY)"

    def test_default_placeholder_format(self):
        from python.helpers.secrets import alias_for_key

        assert alias_for_key("foo") == "§§secret(FOO)"

    def test_custom_placeholder_format(self):
        from python.helpers.secrets import alias_for_key

        result = alias_for_key("bar", placeholder="{{secret:{key}}}")
        assert result == "{{secret:BAR}}"


# --- ALIAS_PATTERN ---


class TestAliasPattern:
    def test_matches_valid_placeholder(self):
        from python.helpers.secrets import ALIAS_PATTERN

        m = re.search(ALIAS_PATTERN, "Use §§secret(API_KEY) here")
        assert m is not None
        assert m.group(1) == "API_KEY"

    def test_matches_lowercase_key(self):
        from python.helpers.secrets import ALIAS_PATTERN

        m = re.search(ALIAS_PATTERN, "§§secret(api_key)")
        assert m is not None
        assert m.group(1) == "api_key"

    def test_matches_underscore_key(self):
        from python.helpers.secrets import ALIAS_PATTERN

        m = re.search(ALIAS_PATTERN, "§§secret(MY_SECRET_KEY)")
        assert m is not None
        assert m.group(1) == "MY_SECRET_KEY"

    def test_no_match_plain_text(self):
        from python.helpers.secrets import ALIAS_PATTERN

        assert re.search(ALIAS_PATTERN, "no placeholder here") is None


# --- StreamingSecretsFilter ---


class TestStreamingSecretsFilter:
    def test_process_chunk_replaces_full_secret(self):
        from python.helpers.secrets import StreamingSecretsFilter

        f = StreamingSecretsFilter({"API_KEY": "sk-abc123"})
        result = f.process_chunk("The key is sk-abc123")
        assert "sk-abc123" not in result
        assert "§§secret(API_KEY)" in result

    def test_process_chunk_holds_partial_prefix(self):
        from python.helpers.secrets import StreamingSecretsFilter

        f = StreamingSecretsFilter({"API_KEY": "sk-abc123"}, min_trigger=3)
        # Send "sk-" which is a prefix of the secret
        out1 = f.process_chunk("The key is sk-")
        assert "sk-" not in out1  # held in buffer
        out2 = f.process_chunk("abc123")
        assert "sk-abc123" not in (out1 + out2)
        assert "§§secret(API_KEY)" in (out1 + out2)

    def test_finalize_masks_unresolved_partial(self):
        from python.helpers.secrets import StreamingSecretsFilter

        f = StreamingSecretsFilter({"API_KEY": "sk-abc123"}, min_trigger=3)
        f.process_chunk("The key is sk-")
        result = f.finalize()
        assert "***" in result
        assert "sk-" not in result

    def test_finalize_empty_when_no_pending(self):
        from python.helpers.secrets import StreamingSecretsFilter

        f = StreamingSecretsFilter({"API_KEY": "secret"})
        f.process_chunk("hello")
        f.process_chunk("")  # flush
        result = f.finalize()
        assert result == ""

    def test_empty_chunk_returns_empty(self):
        from python.helpers.secrets import StreamingSecretsFilter

        f = StreamingSecretsFilter({"K": "val"})
        assert f.process_chunk("") == ""

    def test_nested_secrets_longest_first(self):
        from python.helpers.secrets import StreamingSecretsFilter

        # "short" is substring of "shortsecret"
        f = StreamingSecretsFilter({"A": "shortsecret", "B": "short"})
        result = f.process_chunk("x shortsecret y short z")
        assert "shortsecret" not in result
        assert "short" not in result
        assert "§§secret(A)" in result
        assert "§§secret(B)" in result

    def test_ignores_empty_values(self):
        from python.helpers.secrets import StreamingSecretsFilter

        f = StreamingSecretsFilter({"K1": "val", "K2": ""})
        result = f.process_chunk("val")
        assert "§§secret(K1)" in result
        assert "val" not in result


# --- SecretsManager ---


class TestSecretsManagerGetInstance:
    def test_singleton_per_files_tuple(self):
        from python.helpers.secrets import SecretsManager

        a = SecretsManager.get_instance("a.env")
        b = SecretsManager.get_instance("a.env")
        assert a is b

    def test_different_files_different_instances(self):
        from python.helpers.secrets import SecretsManager

        a = SecretsManager.get_instance("a.env")
        b = SecretsManager.get_instance("b.env")
        assert a is not b

    def test_default_file_when_empty(self):
        from python.helpers.secrets import SecretsManager, DEFAULT_SECRETS_FILE

        m = SecretsManager.get_instance()
        assert m._files == (DEFAULT_SECRETS_FILE,)


class TestSecretsManagerReadSecretsRaw:
    def test_reads_single_file(self, mock_files):
        from python.helpers.secrets import SecretsManager

        mock_files.read_file.return_value = "API_KEY=secret123"
        m = SecretsManager("usr/secrets.env")
        result = m.read_secrets_raw()
        assert result == "API_KEY=secret123"
        mock_files.read_file.assert_called_with("usr/secrets.env")

    def test_reads_multiple_files_joined(self, mock_files):
        from python.helpers.secrets import SecretsManager

        mock_files.read_file.side_effect = ["A=1", "B=2"]
        m = SecretsManager("f1.env", "f2.env")
        result = m.read_secrets_raw()
        assert result == "A=1\nB=2"

    def test_handles_read_exception(self, mock_files):
        from python.helpers.secrets import SecretsManager

        mock_files.read_file.side_effect = OSError("not found")
        m = SecretsManager("missing.env")
        result = m.read_secrets_raw()
        assert result == ""


class TestSecretsManagerLoadSecrets:
    def test_parses_env_content(self, mock_files):
        from python.helpers.secrets import SecretsManager

        mock_files.read_file.return_value = "API_KEY=sk-123\nOTHER=val"
        m = SecretsManager("usr/secrets.env")
        secrets = m.load_secrets()
        assert secrets["API_KEY"] == "sk-123"
        assert secrets["OTHER"] == "val"

    def test_keys_uppercased(self, mock_files):
        from python.helpers.secrets import SecretsManager

        mock_files.read_file.return_value = "api_key=secret"
        m = SecretsManager("usr/secrets.env")
        secrets = m.load_secrets()
        assert "API_KEY" in secrets
        assert secrets["API_KEY"] == "secret"

    def test_caches_result(self, mock_files):
        from python.helpers.secrets import SecretsManager

        mock_files.read_file.return_value = "K=v"
        m = SecretsManager("usr/secrets.env")
        m.load_secrets()
        m.load_secrets()
        assert mock_files.read_file.call_count == 1

    def test_empty_content_returns_empty_dict(self, mock_files):
        from python.helpers.secrets import SecretsManager

        mock_files.read_file.return_value = ""
        m = SecretsManager("usr/secrets.env")
        assert m.load_secrets() == {}


class TestSecretsManagerSaveSecrets:
    def test_saves_content(self, mock_files):
        from python.helpers.secrets import SecretsManager

        m = SecretsManager("usr/secrets.env")
        m.save_secrets("API_KEY=newval")
        mock_files.write_file.assert_called_once()
        call_args = mock_files.write_file.call_args
        assert call_args[0][0] == "usr/secrets.env"
        assert call_args[0][1] == "API_KEY=newval"

    def test_raises_for_multiple_files(self, mock_files):
        from python.helpers.secrets import SecretsManager

        m = SecretsManager("f1.env", "f2.env")
        with pytest.raises(RuntimeError, match="single secrets file"):
            m.save_secrets("K=v")


class TestSecretsManagerSaveSecretsWithMerge:
    def test_merge_preserves_masked_values(self, mock_files):
        from python.helpers.secrets import SecretsManager

        mock_files.read_file.return_value = "API_KEY=actual_secret"
        m = SecretsManager("usr/secrets.env")
        m._last_raw_text = "API_KEY=actual_secret"
        m.save_secrets_with_merge("API_KEY=***")
        call_args = mock_files.write_file.call_args
        written = call_args[0][1]
        assert "actual_secret" in written
        assert "API_KEY" in written

    def test_merge_deletes_omitted_keys(self, mock_files):
        from python.helpers.secrets import SecretsManager

        existing = "OLD_KEY=oldval\n"
        mock_files.read_file.return_value = existing
        m = SecretsManager("usr/secrets.env")
        m._last_raw_text = existing
        m.save_secrets_with_merge("NEW_KEY=newval")
        written = mock_files.write_file.call_args[0][1]
        assert "OLD_KEY" not in written
        assert "NEW_KEY" in written

    def test_merge_ignores_masked_only_new_key(self, mock_files):
        from python.helpers.secrets import SecretsManager

        m = SecretsManager("usr/secrets.env")
        m._last_raw_text = ""
        m.save_secrets_with_merge("NEW_KEY=***")
        written = mock_files.write_file.call_args[0][1]
        assert "NEW_KEY" not in written

    def test_merge_raises_repairable_when_read_fails_and_masked_present(self, mock_files):
        from python.helpers.secrets import SecretsManager
        from python.helpers.errors import RepairableException

        mock_files.read_file.side_effect = OSError("read failed")
        m = SecretsManager("usr/secrets.env")
        m._last_raw_text = None
        with pytest.raises(RepairableException, match="could not be read"):
            m.save_secrets_with_merge("API_KEY=***")

    def test_merge_raises_for_multiple_files(self, mock_files):
        from python.helpers.secrets import SecretsManager

        m = SecretsManager("f1.env", "f2.env")
        with pytest.raises(RuntimeError, match="multiple files"):
            m.save_secrets_with_merge("K=v")


class TestSecretsManagerReplacePlaceholders:
    def test_replaces_placeholder_with_value(self, mock_files):
        from python.helpers.secrets import SecretsManager

        mock_files.read_file.return_value = "API_KEY=secret123"
        m = SecretsManager("usr/secrets.env")
        result = m.replace_placeholders("Use §§secret(API_KEY) here")
        assert result == "Use secret123 here"

    def test_raises_for_unknown_placeholder(self, mock_files):
        from python.helpers.secrets import SecretsManager
        from python.helpers.errors import RepairableException

        mock_files.read_file.return_value = "API_KEY=secret"
        m = SecretsManager("usr/secrets.env")
        with pytest.raises(RepairableException, match="not found"):
            m.replace_placeholders("§§secret(UNKNOWN_KEY)")

    def test_empty_text_returns_unchanged(self, mock_files):
        from python.helpers.secrets import SecretsManager

        m = SecretsManager("usr/secrets.env")
        assert m.replace_placeholders("") == ""


class TestSecretsManagerMaskValues:
    def test_masks_secret_values(self, mock_files):
        from python.helpers.secrets import SecretsManager

        mock_files.read_file.return_value = "API_KEY=sk-12345"
        m = SecretsManager("usr/secrets.env")
        result = m.mask_values("The key is sk-12345")
        assert "sk-12345" not in result
        assert "§§secret(API_KEY)" in result

    def test_respects_min_length(self, mock_files):
        from python.helpers.secrets import SecretsManager

        mock_files.read_file.return_value = "SHORT=abc"
        m = SecretsManager("usr/secrets.env")
        result = m.mask_values("The value is abc", min_length=4)
        assert "abc" in result  # len 3 < 4, not masked

    def test_empty_text_returns_unchanged(self, mock_files):
        from python.helpers.secrets import SecretsManager

        m = SecretsManager("usr/secrets.env")
        assert m.mask_values("") == ""


class TestSecretsManagerGetMaskedSecrets:
    def test_masks_values_for_display(self, mock_files):
        from python.helpers.secrets import SecretsManager

        mock_files.read_file.return_value = "API_KEY=secret123\n# comment"
        m = SecretsManager("usr/secrets.env")
        result = m.get_masked_secrets()
        assert "secret123" not in result
        assert "***" in result
        assert "# comment" in result


class TestSecretsManagerParseEnvContent:
    def test_parses_key_value_pairs(self):
        from python.helpers.secrets import SecretsManager

        m = SecretsManager("x.env")
        result = m.parse_env_content("FOO=bar\nBAZ=qux")
        assert result == {"FOO": "bar", "BAZ": "qux"}

    def test_uppercases_keys(self):
        from python.helpers.secrets import SecretsManager

        m = SecretsManager("x.env")
        result = m.parse_env_content("foo=bar")
        assert result == {"FOO": "bar"}

    def test_empty_value(self):
        from python.helpers.secrets import SecretsManager

        m = SecretsManager("x.env")
        result = m.parse_env_content("EMPTY=")
        assert result.get("EMPTY") == ""


class TestSecretsManagerParseEnvLines:
    def test_parses_pairs_comments_blanks(self):
        from python.helpers.secrets import SecretsManager

        content = "KEY=val\n# comment\n\nOTHER=val2"
        m = SecretsManager("x.env")
        lines = m.parse_env_lines(content)
        types = [ln.type for ln in lines]
        assert "pair" in types
        assert "comment" in types
        assert "blank" in types

    def test_pair_has_key_and_value(self):
        from python.helpers.secrets import SecretsManager

        m = SecretsManager("x.env")
        lines = m.parse_env_lines("MY_KEY=my_value")
        pair = next(ln for ln in lines if ln.type == "pair")
        assert pair.key == "MY_KEY"
        assert pair.value == "my_value"


class TestSecretsManagerClearCache:
    def test_clears_cache(self, mock_files):
        from python.helpers.secrets import SecretsManager

        mock_files.read_file.return_value = "K=v"
        m = SecretsManager("usr/secrets.env")
        m.load_secrets()
        m.clear_cache()
        m.load_secrets()
        assert mock_files.read_file.call_count == 2


class TestSecretsManagerGetKeys:
    def test_returns_key_list(self, mock_files):
        from python.helpers.secrets import SecretsManager

        mock_files.read_file.return_value = "A=1\nB=2"
        m = SecretsManager("usr/secrets.env")
        keys = m.get_keys()
        assert set(keys) == {"A", "B"}


class TestSecretsManagerCreateStreamingFilter:
    def test_creates_filter_with_current_secrets(self, mock_files):
        from python.helpers.secrets import SecretsManager

        mock_files.read_file.return_value = "API_KEY=secret"
        m = SecretsManager("usr/secrets.env")
        f = m.create_streaming_filter()
        assert f is not None
        result = f.process_chunk("secret")
        assert "§§secret(API_KEY)" in result


class TestSecretsManagerChangePlaceholders:
    def test_changes_placeholder_format(self, mock_files):
        from python.helpers.secrets import SecretsManager

        mock_files.read_file.return_value = "API_KEY=secret"
        m = SecretsManager("usr/secrets.env")
        text = "Use §§secret(API_KEY) here"
        result = m.change_placeholders(text, new_format="{{SECRET:{key}}}")
        assert "{{SECRET:API_KEY}}" in result
        assert "§§secret" not in result


# --- get_secrets_manager, get_project_secrets_manager, get_default_secrets_manager ---


class TestGetSecretsManager:
    def test_get_default_secrets_manager(self):
        from python.helpers.secrets import get_default_secrets_manager, DEFAULT_SECRETS_FILE

        m = get_default_secrets_manager()
        assert m._files == (DEFAULT_SECRETS_FILE,)

    def test_get_project_secrets_manager(self):
        with patch("python.helpers.secrets.projects") as mock_proj:
            mock_proj.get_project_meta_folder.return_value = "/proj/meta"
            with patch("python.helpers.secrets.files") as mock_files:
                mock_files.get_abs_path.return_value = "/proj/meta/secrets.env"
                from python.helpers.secrets import get_project_secrets_manager

                m = get_project_secrets_manager("myproject")
                assert "secrets.env" in str(m._files[-1])

    def test_get_project_secrets_manager_merge_with_global(self):
        with patch("python.helpers.secrets.projects") as mock_proj:
            mock_proj.get_project_meta_folder.return_value = "/proj/meta"
            with patch("python.helpers.secrets.files") as mock_files:
                mock_files.get_abs_path.return_value = "/proj/meta/secrets.env"
                from python.helpers.secrets import get_project_secrets_manager, DEFAULT_SECRETS_FILE

                m = get_project_secrets_manager("myproject", merge_with_global=True)
                assert len(m._files) == 2
                assert m._files[0] == DEFAULT_SECRETS_FILE
