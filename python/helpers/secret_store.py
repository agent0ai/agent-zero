"""
SecretStore - caching and change notification for secret backends.

Provides a unified interface over any SecretBackend with:
- Thread-safe operations
- TTL-based caching
- Change listeners for hot-reload
- Migration and import/export utilities
"""

import threading
import time
import json
from typing import Dict, Optional, Callable, List
from dataclasses import dataclass, field

from .secret_backends import SecretBackend


@dataclass
class SecretStore:
    """Unified secret store with caching and change tracking."""

    backend: SecretBackend
    _cache: Optional[Dict[str, str]] = field(default=None, init=False)
    _cache_timestamp: float = field(default=0.0, init=False)
    _cache_ttl: float = 5.0  # seconds
    _lock: threading.RLock = field(default_factory=threading.RLock)
    _change_listeners: list = field(default_factory=list, init=False)

    def get_secrets(self, force_reload: bool = False) -> Dict[str, str]:
        """Get all secrets, using cache if available and not expired."""
        with self._lock:
            now = time.time()
            if (
                force_reload
                or self._cache is None
                or now - self._cache_timestamp > self._cache_ttl
            ):
                self._cache = self.backend.get_secrets()
                self._cache_timestamp = now
                self._notify_change()
            return self._cache.copy()  # Return copy to prevent mutation

    def get_secret(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get a single secret."""
        secrets = self.get_secrets()
        return secrets.get(key.upper(), default)

    def set_secret(self, key: str, value: str) -> None:
        """Set a secret and immediately save."""
        with self._lock:
            secrets = self.get_secrets(force_reload=True)
            secrets[key.upper()] = value
            self.backend.save_secrets(secrets)
            self._cache = secrets
            self._cache_timestamp = time.time()

    def delete_secret(self, key: str) -> None:
        """Delete a secret."""
        with self._lock:
            secrets = self.get_secrets(force_reload=True)
            key_upper = key.upper()
            if key_upper in secrets:
                del secrets[key_upper]
                self.backend.save_secrets(secrets)
                self._cache = secrets
                self._cache_timestamp = time.time()

    def get_available_keys(self) -> List[str]:
        """List all available secret keys."""
        return self.backend.get_available_keys()

    @property
    def backend_name(self) -> str:
        """Get backend name."""
        return self.backend.backend_name

    def clear_cache(self) -> None:
        """Clear the cache."""
        with self._lock:
            self._cache = None
            self._cache_timestamp = 0.0

    def add_change_listener(self, callback: Callable[[], None]) -> None:
        """Add a callback to be notified when secrets change."""
        self._change_listeners.append(callback)

    def remove_change_listener(self, callback: Callable[[], None]) -> None:
        """Remove a change listener."""
        if callback in self._change_listeners:
            self._change_listeners.remove(callback)

    def _notify_change(self) -> None:
        """Notify all listeners of secret changes."""
        for callback in self._change_listeners:
            try:
                callback()
            except Exception:
                pass  # Don't let listener errors break the store

    def migrate_from(self, source_backend: SecretBackend) -> None:
        """Migrate secrets from another backend."""
        source_secrets = source_backend.get_secrets()
        if source_secrets:
            current_secrets = self.get_secrets(force_reload=True)
            # Merge, source takes precedence for overlapping keys
            current_secrets.update(source_secrets)
            self.backend.save_secrets(current_secrets)
            self._cache = current_secrets
            self._cache_timestamp = time.time()

    def export_plaintext(self) -> str:
        """Export secrets as plaintext .env format (for migration backup)."""
        secrets = self.get_secrets()
        lines = []
        for key, value in secrets.items():
            if any(c in value for c in ['"', "'", '\\', '\n']):
                value = json.dumps(value)
            lines.append(f"{key}={value}")
        return "\n".join(lines) + "\n"

    def import_plaintext(self, content: str, merge: bool = True) -> None:
        """Import secrets from plaintext .env format."""
        from dotenv import parse_stream
        from io import StringIO

        incoming = {}
        for binding in parse_stream(StringIO(content)):
            if binding.key and not binding.error:
                incoming[binding.key.upper()] = binding.value or ""

        if merge:
            secrets = self.get_secrets(force_reload=True)
            secrets.update(incoming)
        else:
            secrets = incoming

        self.backend.save_secrets(secrets)
        self._cache = secrets
        self._cache_timestamp = time.time()
