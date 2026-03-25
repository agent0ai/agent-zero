"""
Secret management system with pluggable secure storage backends.

This module provides backward-compatible SecretsManager that now supports:
- Plaintext .env files (current default)
- AES-GCM encrypted .env files
- Docker secrets (from /run/secrets/)
- OS keyring storage

All existing APIs remain unchanged for backward compatibility.
"""

import re
import threading
import time
import os
import json
from io import StringIO
from dataclasses import dataclass
from typing import Dict, Optional, List, Literal, Set, Callable, Tuple, TYPE_CHECKING
from dotenv.parser import parse_stream

from .errors import RepairableException
from .files import get_abs_path, read_file, write_file
from .secret_backends import SecretBackend, PlaintextBackend, get_secret_backend
from .secret_store import SecretStore

if TYPE_CHECKING:
    from agent import AgentContext


# New alias-based placeholder format §§secret(KEY)
ALIAS_PATTERN = r"§§secret\(([A-Za-z_][A-Za-z0-9_]*)\)"
DEFAULT_SECRETS_FILE = "usr/secrets.env"
DEFAULT_SECRETS_BACKEND = os.getenv("SECRETS_BACKEND", "plaintext")


def alias_for_key(key: str, placeholder: str = "§§secret({key})") -> str:
    """Return alias string for given key in upper-case."""
    key = key.upper()
    return placeholder.format(key=key)


@dataclass
class EnvLine:
    raw: str
    type: Literal["pair", "comment", "blank", "other"]
    key: Optional[str] = None
    value: Optional[str] = None
    inline_comment: Optional[str] = None


class StreamingSecretsFilter:
    """Stateful streaming filter that masks secrets on the fly."""

    def __init__(self, key_to_value: Dict[str, str], min_trigger: int = 3):
        self.min_trigger = max(1, int(min_trigger))
        self.value_to_key: Dict[str, str] = {
            v: k for k, v in key_to_value.items() if isinstance(v, str) and v
        }
        self.secret_values: List[str] = [v for v in self.value_to_key.keys() if v]
        self.prefixes: Set[str] = set()
        for v in self.secret_values:
            for i in range(self.min_trigger, len(v) + 1):
                self.prefixes.add(v[:i])
        self.max_len: int = max((len(v) for v in self.secret_values), default=0)
        self.pending: str = ""

    def _replace_full_values(self, text: str) -> str:
        for val in sorted(self.secret_values, key=len, reverse=True):
            if not val:
                continue
            key = self.value_to_key.get(val, "")
            if key:
                text = text.replace(val, alias_for_key(key))
        return text

    def _longest_suffix_prefix(self, text: str) -> int:
        max_check = min(len(text), self.max_len)
        for length in range(max_check, self.min_trigger - 1, -1):
            suffix = text[-length:]
            if suffix in self.prefixes:
                return length
        return 0

    def process_chunk(self, chunk: str) -> str:
        if not chunk:
            return ""
        self.pending += chunk
        self.pending = self._replace_full_values(self.pending)
        hold_len = self._longest_suffix_prefix(self.pending)
        if hold_len > 0:
            emit = self.pending[:-hold_len]
            self.pending = self.pending[-hold_len:]
        else:
            emit = self.pending
            self.pending = ""
        return emit

    def finalize(self) -> str:
        if not self.pending:
            return ""
        hold_len = self._longest_suffix_prefix(self.pending)
        if hold_len > 0:
            safe = self.pending[:-hold_len]
            result = safe + "***"
        else:
            result = self.pending
        self.pending = ""
        return result


class SecretsManager:
    """
    Manages secrets with support for multiple backends and file merging.

    This class provides a unified interface regardless of the backend used.
    It maintains full backward compatibility with the original implementation.
    """

    PLACEHOLDER_PATTERN = ALIAS_PATTERN
    MASK_VALUE = "***"

    _instances: Dict[Tuple[str, ...], "SecretsManager"] = {}

    @classmethod
    def get_instance(cls, *secrets_files: str) -> "SecretsManager":
        """Get or create a SecretsManager instance for the given files."""
        if not secrets_files:
            secrets_files = (DEFAULT_SECRETS_FILE,)
        key = tuple(secrets_files)
        if key not in cls._instances:
            cls._instances[key] = cls(*secrets_files)
        return cls._instances[key]

    def __init__(self, *files: str):
        self._lock = threading.RLock()
        self._files: Tuple[str, ...] = tuple(files) if files else (DEFAULT_SECRETS_FILE,)

        # Determine backend from environment or default to plaintext
        backend_name = os.getenv("SECRETS_BACKEND", DEFAULT_SECRETS_BACKEND)

        # For multiple files, only the primary (first) file uses the configured backend.
        # Additional files (like project-specific secrets) remain plaintext for simplicity.
        # This maintains compatibility while allowing encryption of main secrets.
        primary_file = self._files[0]
        try:
            # Try to create the configured backend for primary file
            backend = get_secret_backend(backend_name, secrets_file=primary_file)
        except Exception as e:
            # Fall back to plaintext if backend fails to initialize
            # (e.g., missing dependencies, invalid configuration)
            print(f"Warning: Failed to initialize secret backend '{backend_name}': {e}")
            print("Falling back to plaintext backend.")
            backend = PlaintextBackend(secrets_file=primary_file)

        # For multiple files, we wrap the backend to handle merging
        if len(self._files) > 1:
            self._store = self._create_composite_store(backend, self._files[1:])
        else:
            self._store = SecretStore(backend)

        self._raw_snapshots: Dict[str, str] = {}
        self._last_raw_text: Optional[str] = None

    def _create_composite_store(self, primary_backend: SecretBackend, secondary_files: Tuple[str, ...]) -> SecretStore:
        """Create a SecretStore that merges primary (encrypted) + secondary (plaintext) backends."""
        # For simplicity, secondary files use plaintext backend
        # The composite store reads from all, writes only to primary

        class CompositeStore(SecretStore):
            def __init__(self, primary_b: SecretBackend, secondary_fns: Tuple[str, ...]):
                # Don't call super - we override all methods
                self.primary = primary_b
                self.secondary_backends = [PlaintextBackend(file) for file in secondary_fns]
                self._cache = None
                self._cache_timestamp = 0.0
                self._cache_ttl = 5.0
                self._lock = threading.RLock()
                self._change_listeners = []

            def get_secrets(self, force_reload: bool = False) -> Dict[str, str]:
                with self._lock:
                    now = time.time()
                    if force_reload or self._cache is None or now - self._cache_timestamp > self._cache_ttl:
                        # Load from all backends, combine
                        all_secrets = {}
                        # Primary first (takes precedence)
                        try:
                            all_secrets.update(self.primary.get_secrets())
                        except Exception:
                            pass
                        # Then secondary (can override if primary doesn't have key)
                        for sec in self.secondary_backends:
                            try:
                                sec_secrets = sec.get_secrets()
                                for k, v in sec_secrets.items():
                                    if k not in all_secrets:  # Don't override primary
                                        all_secrets[k] = v
                            except Exception:
                                continue
                        self._cache = all_secrets
                        self._cache_timestamp = now
                        self._notify_change()
                    return self._cache.copy()

            def save_secrets(self, secrets: Dict[str, str]) -> None:
                # Only save to primary backend
                self.primary.save_secrets(secrets)
                self._cache = secrets
                self._cache_timestamp = time.time()

            def get_available_keys(self) -> List[str]:
                keys = []
                try:
                    keys.extend(self.primary.get_available_keys())
                except Exception:
                    pass
                for sec in self.secondary_backends:
                    try:
                        keys.extend(sec.get_available_keys())
                    except Exception:
                        continue
                return list(set(keys))

            @property
            def backend_name(self) -> str:
                return f"composite({self.primary.backend_name})"

        return CompositeStore(primary_backend, secondary_files)

    # ------------------------------------------------------------------------
    # Public API - These methods maintain backward compatibility
    # ------------------------------------------------------------------------

    def read_secrets_raw(self) -> str:
        """Read raw secrets file content from local filesystem."""
        with self._store._lock:
            # For composite store, we need to reconstruct raw .env format
            # We get all secrets and format them, but this loses comments
            # For true raw reading with multiple files, we'd need to read each file individually
            if len(self._files) == 1:
                try:
                    content = read_file(self._files[0])
                except Exception:
                    content = ""
                self._last_raw_text = content
                return content
            else:
                # For composite, return primary file content (used for merging)
                try:
                    content = read_file(self._files[0])
                except Exception:
                    content = ""
                self._last_raw_text = content
                return content

    def _write_secrets_raw(self, content: str):
        """Write raw secrets file content to local filesystem."""
        if len(self._store._files if hasattr(self._store, '_files') else self._files) != 1:
            raise RuntimeError("Saving secrets content is only supported for a single secrets file")
        # Use the primary file
        write_file(self._files[0], content)

    def load_secrets(self) -> Dict[str, str]:
        """Load secrets from store, return key-value dict."""
        return self._store.get_secrets()

    def save_secrets(self, secrets_content: str):
        """Save secrets content to file and update cache."""
        with self._store._lock:
            # Parse the incoming content and save as key-value
            parsed = self.parse_env_content(secrets_content)
            self._store.save_secrets(parsed)
            self._invalidate_all_caches()

    def save_secrets_with_merge(self, submitted_content: str):
        """Merge submitted content with existing file preserving comments, order and supporting deletion."""
        if len(self._files) != 1:
            raise RuntimeError("Merging secrets is disabled when multiple files are configured")
        with self._lock:
            # Use in-memory snapshot to avoid disk reads
            if self._last_raw_text is not None:
                existing_text = self._last_raw_text
            else:
                try:
                    existing_text = read_file(self._files[0])
                    self._raw_snapshots[self._files[0]] = existing_text
                except Exception as e:
                    if self.MASK_VALUE in submitted_content:
                        raise RepairableException(
                            "Saving secrets failed because existing secrets could not be read to preserve masked values and comments. Please retry."
                        ) from e
                    existing_text = ""
            merged_lines = self._merge_env(existing_text, submitted_content)
            merged_text = self._serialize_env_lines(merged_lines)
            self._write_secrets_raw(merged_text)
        self._invalidate_all_caches()

    def get_keys(self) -> List[str]:
        """Get list of secret keys."""
        return self._store.get_available_keys()

    def get_secrets_for_prompt(self) -> str:
        """Get formatted string of secret keys for system prompt."""
        content = self.read_secrets_raw()
        if not content:
            return ""
        env_lines = self.parse_env_lines(content)
        return self._serialize_env_lines(
            env_lines,
            with_values=False,
            with_comments=True,
            with_blank=True,
            with_other=True,
            key_formatter=alias_for_key,
        )

    def create_streaming_filter(self) -> StreamingSecretsFilter:
        """Create a streaming-aware secrets filter snapshotting current secret values."""
        secrets = self.load_secrets()
        return StreamingSecretsFilter(secrets)

    def replace_placeholders(self, text: str) -> str:
        """Replace secret placeholders with actual values."""
        if not text:
            return text
        secrets = self.load_secrets()
        def replacer(match):
            key = match.group(1).upper()
            if key in secrets:
                return secrets[key]
            else:
                available_keys = ", ".join(secrets.keys())
                error_msg = f"Secret placeholder '{alias_for_key(key)}' not found in secrets store.\n"
                error_msg += f"Available secrets: {available_keys}"
                raise RepairableException(error_msg)
        return re.sub(self.PLACEHOLDER_PATTERN, replacer, text)

    def change_placeholders(self, text: str, new_format: str) -> str:
        """Substitute secret placeholders with a different placeholder format."""
        if not text:
            return text
        secrets = self.load_secrets()
        result = text
        for key, _value in sorted(secrets.items(), key=lambda x: len(x[1]), reverse=True):
            result = result.replace(alias_for_key(key), new_format.format(key=key))
        return result

    def mask_values(self, text: str, min_length: int = 4, placeholder: str = "§§secret({key})") -> str:
        """Replace actual secret values with placeholders in text."""
        if not text:
            return text
        secrets = self.load_secrets()
        result = text
        for key, value in sorted(secrets.items(), key=lambda x: len(str(x[1])), reverse=True):
            val = str(value)
            if val and len(val.strip()) >= min_length:
                result = result.replace(val, alias_for_key(key, placeholder))
        return result

    def get_masked_secrets(self) -> str:
        """Get content with values masked for frontend display."""
        content = self.read_secrets_raw()
        if not content:
            return ""
        secrets_map = self.parse_env_content(content)
        env_lines = self.parse_env_lines(content)
        for ln in env_lines:
            if ln.type == "pair" and ln.key is not None:
                ln.key = ln.key.upper()
                if ln.key in secrets_map and secrets_map[ln.key] != "":
                    ln.value = self.MASK_VALUE
        return self._serialize_env_lines(env_lines)

    def parse_env_content(self, content: str) -> Dict[str, str]:
        """Parse .env format content into key-value dict."""
        env: Dict[str, str] = {}
        for binding in parse_stream(StringIO(content)):
            if binding.key and not binding.error:
                env[binding.key.upper()] = binding.value or ""
        return env

    def clear_cache(self):
        """Clear the secrets cache."""
        with self._store._lock:
            self._store.clear_cache()

    @classmethod
    def _invalidate_all_caches(cls):
        for instance in cls._instances.values():
            instance.clear_cache()

    # ---------------- Internal helpers ----------------

    def parse_env_lines(self, content: str) -> List[EnvLine]:
        """Parse env file into EnvLine objects preserving comments and order."""
        lines: List[EnvLine] = []
        for binding in parse_stream(StringIO(content)):
            orig = getattr(binding, "original", None)
            raw = getattr(orig, "string", "") if orig is not None else ""
            if binding.key and not binding.error:
                line_text = raw.rstrip("\n")
                if "=" in line_text:
                    left, right = line_text.split("=", 1)
                else:
                    right = ""
                in_single = False
                in_double = False
                esc = False
                comment_index = None
                for i, ch in enumerate(right):
                    if esc:
                        esc = False
                        continue
                    if ch == "\\":
                        esc = True
                        continue
                    if ch == "'" and not in_double:
                        in_single = not in_single
                        continue
                    if ch == '"' and not in_single:
                        in_double = not in_double
                        continue
                    if ch == "#" and not in_single and not in_double:
                        comment_index = i
                        break
                inline_comment = None
                if comment_index is not None:
                    inline_comment = right[comment_index:]
                lines.append(
                    EnvLine(
                        raw=line_text,
                        type="pair",
                        key=binding.key,
                        value=binding.value or "",
                        inline_comment=inline_comment,
                    )
                )
            else:
                raw_line = raw.rstrip("\n")
                if raw_line.strip() == "":
                    lines.append(EnvLine(raw=raw_line, type="blank"))
                elif raw_line.lstrip().startswith("#"):
                    lines.append(EnvLine(raw=raw_line, type="comment"))
                else:
                    lines.append(EnvLine(raw=raw_line, type="other"))
        return lines

    def _serialize_env_lines(
        self,
        lines: List[EnvLine],
        with_values=True,
        with_comments=True,
        with_blank=True,
        with_other=True,
        key_delimiter="",
        key_formatter: Optional[Callable[[str], str]] = None,
    ) -> str:
        out: List[str] = []
        for ln in lines:
            if ln.type == "pair" and ln.key is not None:
                left = ln.key.upper()
                val = ln.value if ln.value is not None else ""
                comment = ln.inline_comment or ""
                formatted_key = key_formatter(left) if key_formatter else f"{key_delimiter}{left}{key_delimiter}"
                val_part = f'="{val}"' if with_values else ""
                comment_part = f" {comment}" if with_comments and comment else ""
                out.append(f"{formatted_key}{val_part}{comment_part}")
            elif ln.type == "blank" and with_blank:
                out.append(ln.raw)
            elif ln.type == "comment" and with_comments:
                out.append(ln.raw)
            elif ln.type == "other" and with_other:
                out.append(ln.raw)
        return "\n".join(out)

    def _merge_env(self, existing_text: str, submitted_text: str) -> List[EnvLine]:
        """Merge using submitted content as the base preserving comments and structure."""
        existing_lines = self.parse_env_lines(existing_text)
        submitted_lines = self.parse_env_lines(submitted_text)
        existing_pairs: Dict[str, EnvLine] = {
            ln.key: ln
            for ln in existing_lines
            if ln.type == "pair" and ln.key is not None
        }
        merged: List[EnvLine] = []
        for sub in submitted_lines:
            if sub.type != "pair" or sub.key is None:
                merged.append(sub)
                continue
            key = sub.key
            submitted_val = sub.value or ""
            if key in existing_pairs and submitted_val == self.MASK_VALUE:
                existing_val = existing_pairs[key].value or ""
                merged.append(
                    EnvLine(
                        raw=f"{key}={existing_val}",
                        type="pair",
                        key=key,
                        value=existing_val,
                        inline_comment=sub.inline_comment,
                    )
                )
            elif key not in existing_pairs and submitted_val == self.MASK_VALUE:
                continue
            else:
                merged.append(sub)
        return merged

    # Migration helpers
    def migrate_from_plaintext(self, plaintext_file: str) -> None:
        """Migrate secrets from a plaintext file to the current backend."""
        try:
            with open(plaintext_file, 'r') as f:
                content = f.read()
            secrets = self.parse_env_content(content)
            self._store.save_secrets(secrets)
        except Exception as e:
            raise RepairableException(f"Migration failed: {e}")

    def export_plaintext(self) -> str:
        """Export current secrets as plaintext .env format."""
        secrets = self.load_secrets()
        lines = []
        for key, value in secrets.items():
            if any(c in value for c in ['"', "'", '\\', '\n']):
                value = json.dumps(value)
            lines.append(f"{key}={value}")
        return "\n".join(lines) + "\n"

    def import_plaintext(self, content: str, merge: bool = True) -> None:
        """Import secrets from plaintext .env format."""
        incoming = self.parse_env_content(content)
        if merge:
            secrets = self.load_secrets()
            secrets.update(incoming)
        else:
            secrets = incoming
        self._store.save_secrets(secrets)


def get_secrets_manager(context: "AgentContext|None" = None) -> SecretsManager:
    """Get the appropriate SecretsManager instance for the current context."""
    from python.helpers import projects

    secret_files = [DEFAULT_SECRETS_FILE]

    if not context:
        from agent import AgentContext
        context = AgentContext.current()

    if context:
        project = projects.get_context_project_name(context)
        if project:
            secret_files.append(
                files.get_abs_path(projects.get_project_meta_folder(project), "secrets.env")
            )

    return SecretsManager.get_instance(*secret_files)


def get_project_secrets_manager(project_name: str, merge_with_global: bool = False) -> SecretsManager:
    """Get a SecretsManager for a specific project."""
    from python.helpers import projects

    secret_files = []
    if merge_with_global:
        secret_files.append(DEFAULT_SECRETS_FILE)
    secret_files.append(
        files.get_abs_path(projects.get_project_meta_folder(project_name), "secrets.env")
    )
    return SecretsManager.get_instance(*secret_files)


def get_default_secrets_manager() -> SecretsManager:
    """Get the default global SecretsManager."""
    return SecretsManager.get_instance()


# Convenience function to check if encryption is enabled
def is_encrypted_backend() -> bool:
    """Check if the configured backend is encrypted (not plaintext)."""
    backend = os.getenv("SECRETS_BACKEND", DEFAULT_SECRETS_BACKEND)
    return backend != "plaintext"
