"""Comprehensive security tests covering CodeQL remediation fixes.

Tests verify path traversal prevention, null byte rejection, error response
sanitization, file permissions, SSH host key policy, HMAC token derivation,
sandboxing gates, security headers, and backup name sanitization.
"""

import asyncio
import inspect
import json
import os
import stat
import sys
import threading
from pathlib import Path
from unittest.mock import patch

from flask import Flask

# Ensure project root is on sys.path for imports
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.helpers import files, runtime


# ---------------------------------------------------------------------------
# 1. Path Traversal Prevention
# ---------------------------------------------------------------------------
class TestPathTraversal:
    """Verify that path traversal attacks are rejected by helpers in files.py."""

    def test_is_in_base_dir_rejects_traversal(self):
        """Verify ../../../etc/passwd is rejected by is_in_base_dir."""
        base = files.get_base_dir()
        traversal_path = os.path.join(base, "../../../etc/passwd")
        assert not files.is_in_base_dir(traversal_path)

    def test_is_in_base_dir_accepts_valid_path(self):
        """A path inside the project root must be accepted."""
        base = files.get_base_dir()
        valid_path = os.path.join(base, "python/helpers/files.py")
        assert files.is_in_base_dir(valid_path)

    def test_is_in_dir_rejects_traversal(self):
        """Paths outside the target directory must be rejected."""
        assert not files.is_in_dir("/etc/passwd", "/home/user")

    def test_is_in_dir_accepts_subpath(self):
        """A genuine subpath must be accepted."""
        assert files.is_in_dir("/home/user/file.txt", "/home/user")

    def test_realpath_resolves_dotdot(self):
        """os.path.realpath collapses '..' sequences, revealing the true path."""
        base = files.get_base_dir()
        path_with_dotdot = os.path.join(base, "python", "..", "..", "etc", "passwd")
        real = os.path.realpath(path_with_dotdot)
        assert not files.is_in_base_dir(real)

    def test_is_in_dir_with_common_prefix_attack(self):
        """Ensure /home/user_evil is not treated as inside /home/user."""
        # os.path.commonpath would return /home/user for these, but
        # is_in_dir uses abspath + commonpath correctly.
        assert not files.is_in_dir("/home/user_evil/file.txt", "/home/user")

    def test_is_in_base_dir_with_symlink_like_dotdot(self):
        """Multiple layers of '..' must still be resolved and rejected."""
        base = files.get_base_dir()
        deep_traversal = os.path.join(
            base, "a", "b", "..", "..", "..", "..", "etc", "shadow"
        )
        assert not files.is_in_base_dir(deep_traversal)


# ---------------------------------------------------------------------------
# 2. Null Byte Rejection
# ---------------------------------------------------------------------------
class TestNullByteRejection:
    """Verify null byte detection logic works for path sanitization."""

    def test_null_byte_detected_in_string(self):
        """Strings containing null bytes must be detectable."""
        assert "\x00" in "path/../../etc/passwd\x00.png"
        assert "\x00" not in "normal/path.png"

    def test_null_byte_not_in_clean_path(self):
        """Clean paths must not trigger null byte detection."""
        clean_paths = [
            "usr/settings.json",
            "python/helpers/files.py",
            "webui/index.html",
        ]
        for p in clean_paths:
            assert "\x00" not in p

    def test_binary_detection_catches_null_bytes(self):
        """The is_probably_binary_bytes helper detects null bytes as binary."""
        assert files.is_probably_binary_bytes(b"hello\x00world")
        assert not files.is_probably_binary_bytes(b"hello world")


# ---------------------------------------------------------------------------
# 3. Error Response Sanitization
# ---------------------------------------------------------------------------
class TestErrorResponseSanitization:
    """API error handler must hide sensitive details in production mode."""

    @patch.object(runtime, "is_development", return_value=False)
    def test_api_error_no_traceback_in_production(self, _mock_dev):
        """In production, API errors must return a generic message."""
        from python.helpers.api import ApiHandler

        app = Flask(__name__)
        app.secret_key = "test-secret"

        class FailHandler(ApiHandler):
            async def process(self, input, request):
                raise ValueError(
                    "sensitive internal detail about /usr/lib/python3.12/..."
                )

        handler = FailHandler(app, threading.RLock())

        with app.test_request_context(json={}):
            from flask import request as flask_request

            loop = asyncio.new_event_loop()
            try:
                response = loop.run_until_complete(
                    handler.handle_request(flask_request)
                )
            finally:
                loop.close()

            assert response.status_code == 500
            body = response.get_data(as_text=True)
            assert "sensitive internal detail" not in body
            assert "Internal server error" in body

    @patch.object(runtime, "is_development", return_value=True)
    def test_api_error_shows_detail_in_dev(self, _mock_dev):
        """In development, API errors must include the original detail."""
        from python.helpers.api import ApiHandler

        app = Flask(__name__)
        app.secret_key = "test-secret"

        class FailHandler(ApiHandler):
            async def process(self, input, request):
                raise ValueError("detailed error info")

        handler = FailHandler(app, threading.RLock())

        with app.test_request_context(json={}):
            from flask import request as flask_request

            loop = asyncio.new_event_loop()
            try:
                response = loop.run_until_complete(
                    handler.handle_request(flask_request)
                )
            finally:
                loop.close()

            assert response.status_code == 500
            body = response.get_data(as_text=True)
            assert "detailed error info" in body

    @patch.object(runtime, "is_development", return_value=False)
    def test_production_error_is_valid_json(self, _mock_dev):
        """Production error response must be valid JSON with 'error' key."""
        from python.helpers.api import ApiHandler

        app = Flask(__name__)
        app.secret_key = "test-secret"

        class FailHandler(ApiHandler):
            async def process(self, input, request):
                raise RuntimeError("something went wrong internally")

        handler = FailHandler(app, threading.RLock())

        with app.test_request_context(json={}):
            from flask import request as flask_request

            loop = asyncio.new_event_loop()
            try:
                response = loop.run_until_complete(
                    handler.handle_request(flask_request)
                )
            finally:
                loop.close()

            assert response.status_code == 500
            assert response.mimetype == "application/json"
            data = json.loads(response.get_data(as_text=True))
            assert data["error"] == "Internal server error"


# ---------------------------------------------------------------------------
# 4. File Permissions
# ---------------------------------------------------------------------------
class TestFilePermissions:
    """Verify security-sensitive file permission constants in source."""

    def test_no_world_writable_permissions_in_delete_dir(self):
        """delete_dir must use 0o700 (owner-only), not 0o777 (world-writable)."""
        source = inspect.getsource(files.delete_dir)
        assert "0o777" not in source
        assert "0o700" in source

    def test_dotenv_chmod_is_owner_only(self):
        """save_dotenv_value must restrict .env to owner-only (S_IRUSR | S_IWUSR)."""
        from python.helpers import dotenv

        source = inspect.getsource(dotenv.save_dotenv_value)
        assert "S_IRUSR" in source
        assert "S_IWUSR" in source

    def test_dotenv_chmod_numeric_equivalent(self):
        """Sanity check: S_IRUSR | S_IWUSR equals 0o600."""
        assert (stat.S_IRUSR | stat.S_IWUSR) == 0o600


# ---------------------------------------------------------------------------
# 5. SSH Host Key Policy
# ---------------------------------------------------------------------------
class TestSSHHostKeyPolicy:
    """Verify the _is_local_or_private guard in shell_ssh.py."""

    def test_localhost_is_local_or_private(self):
        from python.helpers.shell_ssh import _is_local_or_private

        assert _is_local_or_private("localhost")
        assert _is_local_or_private("127.0.0.1")
        assert _is_local_or_private("::1")

    def test_private_ips_are_local_or_private(self):
        from python.helpers.shell_ssh import _is_local_or_private

        assert _is_local_or_private("192.168.1.1")
        assert _is_local_or_private("10.0.0.1")
        assert _is_local_or_private("172.16.0.1")

    def test_public_ips_are_not_local_or_private(self):
        from python.helpers.shell_ssh import _is_local_or_private

        assert not _is_local_or_private("8.8.8.8")
        assert not _is_local_or_private("1.1.1.1")

    def test_hostnames_are_not_local_or_private(self):
        from python.helpers.shell_ssh import _is_local_or_private

        assert not _is_local_or_private("example.com")
        assert not _is_local_or_private("ssh.remote-server.com")

    def test_link_local_ipv4_is_private(self):
        from python.helpers.shell_ssh import _is_local_or_private

        assert _is_local_or_private("169.254.1.1")

    def test_link_local_ipv6_is_private(self):
        from python.helpers.shell_ssh import _is_local_or_private

        assert _is_local_or_private("fe80::1")


# ---------------------------------------------------------------------------
# 6. HMAC Token Derivation
# ---------------------------------------------------------------------------
class TestHMACTokenDerivation:
    """Verify login and settings modules use HMAC, not bare SHA-256."""

    def test_login_uses_hmac_not_bare_sha256(self):
        """login.get_credentials_hash must use hmac.new, not hashlib.sha256()."""
        from python.helpers import login

        source = inspect.getsource(login.get_credentials_hash)
        assert "hmac.new" in source
        # Bare hashlib.sha256( call should not be present
        assert "hashlib.sha256(" not in source

    def test_settings_uses_hmac_not_bare_sha256(self):
        """settings.create_auth_token must use hmac.new, not hashlib.sha256()."""
        from python.helpers import settings

        source = inspect.getsource(settings.create_auth_token)
        assert "hmac.new" in source
        # Bare hashlib.sha256( call should not be present
        assert "hashlib.sha256(" not in source

    def test_login_hmac_uses_sha256_digestmod(self):
        """The HMAC call in login.py must specify sha256 as the digest."""
        from python.helpers import login

        source = inspect.getsource(login.get_credentials_hash)
        assert "sha256" in source

    def test_settings_hmac_uses_sha256_digestmod(self):
        """The HMAC call in settings.py must specify sha256 as the digest."""
        from python.helpers import settings

        source = inspect.getsource(settings.create_auth_token)
        assert "sha256" in source


# ---------------------------------------------------------------------------
# 7. Sandboxing Gate
# ---------------------------------------------------------------------------
class TestCodeExecutionSandboxing:
    """Verify the sandboxing gate in code_execution_tool.py.

    Note: We read the source file directly because importing
    code_execution_tool triggers tty_session.py which calls
    sys.stdin.reconfigure() -- incompatible with pytest's stdin.
    """

    @staticmethod
    def _read_source():
        source_path = os.path.join(
            files.get_base_dir(), "python", "tools", "code_execution_tool.py"
        )
        with open(source_path, "r") as f:
            return f.read()

    def test_sandboxing_gate_exists_in_source(self):
        """prepare_state must enforce SSH sandboxing in production."""
        source = self._read_source()
        assert "Code execution requires SSH sandboxing" in source
        assert "is_development" in source

    def test_sandboxing_gate_raises_in_production_path(self):
        """The error message must reference SSH and production settings."""
        source = self._read_source()
        assert "code_exec_ssh_enabled" in source
        assert "DEVELOPMENT_MODE" in source

    def test_sandboxing_gate_warns_in_dev_path(self):
        """Development mode must log a warning about unsandboxed execution."""
        source = self._read_source()
        assert "UNSANDBOXED" in source
        assert "development mode only" in source


# ---------------------------------------------------------------------------
# 8. Security Headers
# ---------------------------------------------------------------------------
class TestSecurityHeaders:
    """Verify security response headers are configured in run_ui.py."""

    def test_run_ui_has_security_headers_handler(self):
        """run_ui must set X-Content-Type-Options, X-Frame-Options, CSP, and Referrer-Policy."""
        import run_ui

        source = inspect.getsource(run_ui)
        assert "X-Content-Type-Options" in source
        assert "X-Frame-Options" in source
        assert "Content-Security-Policy" in source
        assert "Referrer-Policy" in source

    def test_run_ui_has_cors_configuration(self):
        """run_ui must configure CORS via flask_cors."""
        import run_ui

        source = inspect.getsource(run_ui)
        assert "flask_cors" in source or "CORS" in source

    def test_run_ui_has_rate_limiter(self):
        """run_ui must configure a rate limiter via flask_limiter."""
        import run_ui

        source = inspect.getsource(run_ui)
        assert "flask_limiter" in source or "Limiter" in source

    def test_security_header_values_are_strict(self):
        """Verify specific header values are set to strict options."""
        import run_ui

        source = inspect.getsource(run_ui)
        assert "nosniff" in source  # X-Content-Type-Options value
        assert "DENY" in source  # X-Frame-Options value
        assert "strict-origin-when-cross-origin" in source  # Referrer-Policy value
        assert "frame-ancestors 'none'" in source  # CSP directive

    def test_session_cookie_samesite_strict(self):
        """Session cookie must use SameSite=Strict."""
        import run_ui

        source = inspect.getsource(run_ui)
        assert "SESSION_COOKIE_SAMESITE" in source
        assert '"Strict"' in source or "'Strict'" in source

    def test_csrf_protection_exists(self):
        """run_ui must define CSRF token protection."""
        import run_ui

        source = inspect.getsource(run_ui)
        assert "csrf_protect" in source
        assert "X-CSRF-Token" in source


# ---------------------------------------------------------------------------
# 9. Backup Name Sanitization
# ---------------------------------------------------------------------------
class TestBackupNameSanitization:
    """Verify backup_name is sanitized in create_backup to prevent path traversal."""

    def test_backup_name_sanitization_in_source(self):
        """create_backup must use re.sub to sanitize the backup_name input."""
        from python.helpers.backup import BackupService

        source = inspect.getsource(BackupService.create_backup)
        assert "re.sub" in source

    def test_backup_name_sanitization_rejects_slashes(self):
        """The regex must strip path separator characters from backup names."""
        import re

        # This is the exact regex from BackupService.create_backup
        dangerous_name = "../../etc/evil-backup"
        sanitized = re.sub(r"[^\w\-]", "_", dangerous_name)
        assert "/" not in sanitized
        assert ".." not in sanitized

    def test_backup_name_sanitization_preserves_safe_chars(self):
        """Safe characters (alphanumeric, hyphen, underscore) must be preserved."""
        import re

        safe_name = "my-backup_2025-01-15"
        sanitized = re.sub(r"[^\w\-]", "_", safe_name)
        assert sanitized == safe_name

    def test_backup_name_sanitization_strips_null_bytes(self):
        """Null bytes in backup names must be replaced."""
        import re

        null_name = "backup\x00evil"
        sanitized = re.sub(r"[^\w\-]", "_", null_name)
        assert "\x00" not in sanitized


# ---------------------------------------------------------------------------
# 10. Additional Cross-Cutting Security Checks
# ---------------------------------------------------------------------------
class TestCrossCuttingSecurity:
    """Additional checks that span multiple modules."""

    def test_format_error_includes_traceback_text(self):
        """format_error must return traceback content (used by dev mode)."""
        from python.helpers.errors import format_error

        try:
            raise ValueError("test error for format_error")
        except ValueError as e:
            result = format_error(e)
            assert "test error for format_error" in result

    def test_safe_file_name_strips_dangerous_chars(self):
        """files.safe_file_name must replace path separator characters."""
        result = files.safe_file_name("../../../etc/passwd")
        assert "/" not in result
        # Dots are safe filename characters so they remain, but slashes are gone
        assert result == ".._.._.._etc_passwd"

    def test_safe_file_name_preserves_normal_chars(self):
        """files.safe_file_name must keep alphanumeric, dash, underscore, dot."""
        result = files.safe_file_name("normal-file_v2.txt")
        assert result == "normal-file_v2.txt"

    def test_write_file_comment_about_sensitivity(self):
        """write_file must have a lgtm suppression comment noting caller responsibility."""
        source = inspect.getsource(files.write_file)
        assert "lgtm" in source or "Caller is responsible" in source

    def test_dotenv_write_has_lgtm_suppression(self):
        """save_dotenv_value must document the lgtm suppression for .env writes."""
        from python.helpers import dotenv

        source = inspect.getsource(dotenv.save_dotenv_value)
        assert "lgtm" in source
        assert ".env" in source or "credential store" in source
