import re
import threading
import time
import os
from io import StringIO
from dataclasses import dataclass
from typing import Dict, Optional, List, Literal, Set, Callable
from dotenv.parser import parse_stream
from python.helpers.errors import RepairableException
from python.helpers import files


# New alias-based placeholder format §§secret(KEY)
ALIAS_PATTERN = r"§§secret\(([A-Za-z_][A-Za-z0-9_]*)\)"

def alias_for_key(key: str, placeholder: str = "§§secret({key})") -> str:
    # Return alias string for given key in upper-case
    key = key.upper()
    return placeholder.format(key=key)

@dataclass
class EnvLine:
    raw: str
    type: Literal["pair", "comment", "blank", "other"]
    key: Optional[str] = None
    value: Optional[str] = None
    key_part: Optional[str] = None  # original left side including whitespace up to '='
    inline_comment: Optional[str] = (
        None  # preserves trailing inline comment including leading spaces and '#'
    )


class StreamingSecretsFilter:
    """Stateful streaming filter that masks secrets on the fly.

    - Replaces full secret values with placeholders §§secret(KEY) when detected.
    - Holds the longest suffix of the current buffer that matches any secret prefix
      (with minimum trigger length of 3) to avoid leaking partial secrets across chunks.
    - On finalize(), any unresolved partial is masked with '***'.
    """

    def __init__(self, key_to_value: Dict[str, str], min_trigger: int = 3):
        self.min_trigger = max(1, int(min_trigger))
        # Map value -> key for placeholder construction
        self.value_to_key: Dict[str, str] = {
            v: k for k, v in key_to_value.items() if isinstance(v, str) and v
        }
        # Only keep non-empty values
        self.secret_values: List[str] = [v for v in self.value_to_key.keys() if v]
        # Precompute all prefixes for quick suffix matching
        self.prefixes: Set[str] = set()
        for v in self.secret_values:
            for i in range(self.min_trigger, len(v) + 1):
                self.prefixes.add(v[:i])
        self.max_len: int = max((len(v) for v in self.secret_values), default=0)

        # Internal buffer of pending text that is not safe to flush yet
        self.pending: str = ""

    def _replace_full_values(self, text: str) -> str:
        """Replace all full secret values with placeholders in the given text."""
        # Sort by length desc to avoid partial overlaps
        for val in sorted(self.secret_values, key=len, reverse=True):
            if not val:
                continue
            key = self.value_to_key.get(val, "")
            if key:
                text = text.replace(val, alias_for_key(key))
        return text

    def _longest_suffix_prefix(self, text: str) -> int:
        """Return length of longest suffix of text that is a known secret prefix.
        Returns 0 if none found (or only shorter than min_trigger)."""
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

        # Replace any full secret occurrences first
        self.pending = self._replace_full_values(self.pending)

        # Determine the longest suffix that could still form a secret
        hold_len = self._longest_suffix_prefix(self.pending)
        if hold_len > 0:
            # Flush everything except the hold suffix
            emit = self.pending[:-hold_len]
            self.pending = self.pending[-hold_len:]
        else:
            # Safe to flush everything
            emit = self.pending
            self.pending = ""

        return emit

    def finalize(self) -> str:
        """Flush any remaining buffered text. If pending contains an unresolved partial
        (i.e., a prefix of a secret >= min_trigger), mask it with *** to avoid leaks."""
        if not self.pending:
            return ""

        hold_len = self._longest_suffix_prefix(self.pending)
        if hold_len > 0:
            safe = self.pending[:-hold_len]
            # Mask unresolved partial
            result = safe + "***"
        else:
            result = self.pending
        self.pending = ""
        return result


class SecretsManager:
    SECRETS_FILE = "tmp/secrets.env"
    PLACEHOLDER_PATTERN = ALIAS_PATTERN
    MASK_VALUE = "***"

    _instance: Optional["SecretsManager"] = None
    _secrets_cache: Optional[Dict[str, str]] = None
    _last_raw_text: Optional[str] = None

    @classmethod
    def get_instance(cls) -> "SecretsManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self._lock = threading.RLock()
        # instance-level override for secrets file
        self._secrets_file_rel = self.SECRETS_FILE

    def set_secrets_file(self, relative_path: str):
        """Override the relative secrets file location (useful for tests)."""
        with self._lock:
            self._secrets_file_rel = relative_path
            self.clear_cache()

    def read_secrets_raw(self) -> str:
        """Read raw secrets file content from local filesystem (same system)."""
        try:
            content = files.read_file(self._secrets_file_rel)
            self._last_raw_text = content
            return content
        except Exception:
            self._last_raw_text = ""
            return ""

    def _write_secrets_raw(self, content: str):
        """Write raw secrets file content to local filesystem."""
        files.write_file(self._secrets_file_rel, content)

    def load_secrets(self) -> Dict[str, str]:
        """Load secrets from file, return key-value dict"""
        with self._lock:
            if self._secrets_cache is not None:
                return self._secrets_cache

            secrets: Dict[str, str] = {}
            try:
                content = self.read_secrets_raw()
                # keep raw snapshot for future save merge without reading again
                self._last_raw_text = content
                if content:
                    secrets = self.parse_env_content(content)
            except Exception as e:
                # On unexpected failure, keep empty cache rather than crash
                secrets = {}

            self._secrets_cache = secrets
            return secrets

    def save_secrets(self, secrets_content: str):
        """Save secrets content to file and update cache"""
        with self._lock:
            # Ensure write to local filesystem (UTF-8)
            self._write_secrets_raw(secrets_content)
            # Update cache
            self._secrets_cache = self.parse_env_content(secrets_content)
            # Update raw snapshot
            self._last_raw_text = secrets_content

    def save_secrets_with_merge(self, submitted_content: str):
        """Merge submitted content with existing file preserving comments, order and supporting deletion.
        - Existing keys keep their value when submitted as MASK_VALUE (***).
        - Keys present in existing but omitted from submitted are deleted.
        - New keys with non-masked values are appended at the end.
        """
        with self._lock:
            # Prefer in-memory snapshot to avoid disk reads during save
            if self._last_raw_text is not None:
                existing_text = self._last_raw_text
            else:
                try:
                    existing_text = self.read_secrets_raw()
                except Exception as e:
                    # If read fails and submitted contains masked values, abort to avoid losing values/comments
                    if self.MASK_VALUE in submitted_content:
                        raise RepairableException(
                            "Saving secrets failed because existing secrets could not be read to preserve masked values and comments. Please retry."
                        ) from e
                    # No masked values, safe to treat as new file
                    existing_text = ""
            merged_lines = self._merge_env(existing_text, submitted_content)
            merged_text = self._serialize_env_lines(merged_lines)
            self.save_secrets(merged_text)

    def get_keys(self) -> List[str]:
        """Get list of secret keys"""
        secrets = self.load_secrets()
        return list(secrets.keys())

    def get_secrets_for_prompt(self) -> str:
        """Get formatted string of secret keys for system prompt"""
        content = self._last_raw_text or self.read_secrets_raw()
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

    def create_streaming_filter(self) -> "StreamingSecretsFilter":
        """Create a streaming-aware secrets filter snapshotting current secret values."""
        return StreamingSecretsFilter(self.load_secrets())

    def replace_placeholders(self, text: str) -> str:
        """Replace secret placeholders with actual values"""
        if not text:
            return text

        secrets = self.load_secrets()

        def replacer(match):
            key = match.group(1)
            key = key.upper()
            if key in secrets:
                return secrets[key]
            else:
                available_keys = ", ".join(secrets.keys())
                error_msg = (
                    f"Secret placeholder '{alias_for_key(key)}' not found in secrets store.\n"
                )
                error_msg += f"Available secrets: {available_keys}"

                raise RepairableException(error_msg)

        return re.sub(self.PLACEHOLDER_PATTERN, replacer, text)

    def change_placeholders(self, text: str, new_format: str) -> str:
        """Substitute secret placeholders with a different placeholder format"""
        if not text:
            return text

        secrets = self.load_secrets()
        result = text

        # Sort by length (longest first) to avoid partial replacements
        for key, _value in sorted(
            secrets.items(), key=lambda x: len(x[1]), reverse=True
        ):
            result = result.replace(alias_for_key(key), new_format.format(key=key))

        return result

    def mask_values(self, text: str, min_length: int = 4, placeholder: str = "§§secret({key})") -> str:
        """Replace actual secret values with placeholders in text"""
        if not text:
            return text

        secrets = self.load_secrets()
        result = text

        # Sort by length (longest first) to avoid partial replacements
        for key, value in sorted(
            secrets.items(), key=lambda x: len(x[1]), reverse=True
        ):
            if value and len(value.strip()) >= min_length:
                result = result.replace(value, alias_for_key(key, placeholder))

        return result

    def get_masked_secrets(self) -> str:
        """Get content with values masked for frontend display (preserves comments and unrecognized lines)"""
        if not (content:=self.read_secrets_raw()):
            return ""

        # Parse content for known keys using python-dotenv
        secrets_map = self.parse_env_content(content)
        env_lines = self.parse_env_lines(content)
        # Replace values with mask for keys present
        for ln in env_lines:
            if ln.type == "pair" and ln.key is not None:
                ln.key = ln.key.upper()
                if ln.key in secrets_map and secrets_map[ln.key] != "":
                    ln.value = self.MASK_VALUE
        return self._serialize_env_lines(env_lines)

    def parse_env_content(self, content: str) -> Dict[str, str]:
        """Parse .env format content into key-value dict using python-dotenv. Keys are always uppercase."""
        env: Dict[str, str] = {}
        for binding in parse_stream(StringIO(content)):
            if binding.key and not binding.error:
                env[binding.key.upper()] = binding.value or ""
        return env

    # Backward-compatible alias for callers using the old private method name
    def _parse_env_content(self, content: str) -> Dict[str, str]:
        return self.parse_env_content(content)

    def clear_cache(self):
        """Clear the secrets cache"""
        with self._lock:
            self._secrets_cache = None

    # ---------------- Internal helpers for parsing/merging ----------------

    def parse_env_lines(self, content: str) -> List[EnvLine]:
        """Parse env file into EnvLine objects using python-dotenv, preserving comments and order.
        We reconstruct key_part and inline_comment based on the original string.
        """
        lines: List[EnvLine] = []
        for binding in parse_stream(StringIO(content)):
            orig = getattr(binding, "original", None)
            raw = getattr(orig, "string", "") if orig is not None else ""
            if binding.key and not binding.error:
                # Determine key_part and inline_comment from original line
                line_text = raw.rstrip("\n")
                # Fallback to composed key_part if original not available
                if "=" in line_text:
                    left, right = line_text.split("=", 1)
                    key_part = left
                else:
                    key_part = binding.key
                    right = ""
                # Try to extract inline comment by scanning right side to comment start, respecting quotes
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
                        key_part=key_part,
                        inline_comment=inline_comment,
                    )
                )
            else:
                # Comment, blank, or other lines
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
                left_raw = ln.key_part if ln.key_part is not None else ln.key
                left = left_raw.upper()
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
        """Merge using submitted content as the base to preserve its comments and structure.
        Behavior:
        - Iterate submitted lines in order and keep them (including comments/blanks/other).
        - For pair lines:
            - If key exists in existing and submitted value is MASK_VALUE (***), use existing value.
            - If key is new and value is MASK_VALUE, skip (ignore masked-only additions).
            - Otherwise, use submitted value as-is.
        - Keys present only in existing and not in submitted are deleted (not added).
        This preserves comments and arbitrary lines from the submitted content and persists them.
        """
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
                # Preserve submitted comments/blanks/other verbatim
                merged.append(sub)
                continue

            key = sub.key
            submitted_val = sub.value or ""

            if key in existing_pairs and submitted_val == self.MASK_VALUE:
                # Replace mask with existing value, keep submitted key formatting
                existing_val = existing_pairs[key].value or ""
                merged.append(
                    EnvLine(
                        raw=f"{(sub.key_part or key)}={existing_val}",
                        type="pair",
                        key=key,
                        value=existing_val,
                        key_part=sub.key_part or key,
                        inline_comment=sub.inline_comment,
                    )
                )
            elif key not in existing_pairs and submitted_val == self.MASK_VALUE:
                # Masked-only new key -> ignore
                continue
            else:
                # Use submitted value as-is
                merged.append(sub)

        return merged
