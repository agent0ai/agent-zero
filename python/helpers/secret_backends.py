"""
Secret storage backends - pluggable secret storage system.

Provides multiple backends for storing secrets securely:
- PlaintextBackend: Current .env file behavior (default during migration)
- EncryptedFileBackend: AES-GCM encrypted .env file
- DockerSecretsBackend: Docker swarm secrets (reads from /run/secrets/)
- KeyringBackend: OS keyring storage
"""

import os
import json
import base64
from abc import ABC, abstractmethod
from typing import Dict, Optional, Any, List
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import secrets as py_secrets

from .files import get_abs_path, read_file, write_file
from .errors import RepairableException


class SecretBackend(ABC):
    """Abstract base class for secret storage backends."""

    @abstractmethod
    def get_secrets(self) -> Dict[str, str]:
        """Load and return all secrets as key-value dict."""
        pass

    @abstractmethod
    def save_secrets(self, secrets: Dict[str, str]) -> None:
        """Save all secrets atomically."""
        pass

    @abstractmethod
    def get_available_keys(self) -> List[str]:
        """List available secret keys."""
        pass

    @property
    @abstractmethod
    def backend_name(self) -> str:
        """Return backend identifier."""
        pass

    def rotate_key(self, old_key: str, new_key: str, value: str) -> None:
        """Helper to rotate a secret key - default implementation loads, modifies, saves."""
        secrets = self.get_secrets()
        if old_key in secrets:
            del secrets[old_key]
        secrets[new_key] = value
        self.save_secrets(secrets)


class PlaintextBackend(SecretBackend):
    """Plaintext .env backend - current implementation for backward compatibility."""

    def __init__(self, secrets_file: str = "usr/secrets.env"):
        self.secrets_file = get_abs_path(secrets_file)

    def get_secrets(self) -> Dict[str, str]:
        """Parse .env file and return key-value dict."""
        from dotenv import parse_stream
        from io import StringIO

        try:
            content = read_file(self.secrets_file)
        except Exception:
            content = ""

        secrets = {}
        for binding in parse_stream(StringIO(content)):
            if binding.key and not binding.error:
                secrets[binding.key.upper()] = binding.value or ""
        return secrets

    def save_secrets(self, secrets: Dict[str, str]) -> None:
        """Write secrets to .env file."""
        lines = []
        for key, value in secrets.items():
            # Escape value if contains special chars
            if any(c in value for c in ['"', "'", '\\', '\n']):
                value = json.dumps(value)
            lines.append(f"{key.upper()}={value}")
        content = "\n".join(lines) + "\n"
        write_file(self.secrets_file, content)

    def get_available_keys(self) -> List[str]:
        return list(self.get_secrets().keys())

    @property
    def backend_name(self) -> str:
        return "plaintext"


class EncryptedFileBackend(SecretBackend):
    """AES-GCM encrypted secrets file backend.

    Uses PBKDF2 to derive encryption key from master password.
    Master password can be provided via ENCRYPTION_KEY env var,
    or derived from a key file, or prompted interactively.
    """

    def __init__(
        self,
        encrypted_file: str = "usr/secrets.enc",
        key_file: Optional[str] = None,
        master_key_env: str = "ENCRYPTION_KEY"
    ):
        self.encrypted_file = get_abs_path(encrypted_file)
        self.key_file = get_abs_path(key_file) if key_file else None
        self.master_key_env = master_key_env
        self._salt_size = 16
        self._nonce_size = 12
        self._kdf_iterations = 100000

    def _derive_key(self, password: bytes, salt: bytes) -> bytes:
        """Derive encryption key from password using PBKDF2."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=self._kdf_iterations,
        )
        return kdf.derive(password)

    def _get_master_password(self) -> bytes:
        """Get master password from env var, key file, or raise error."""
        # Try environment variable first
        env_key = os.getenv(self.master_key_env)
        if env_key:
            return env_key.encode('utf-8')

        # Try key file
        if self.key_file and os.path.exists(self.key_file):
            with open(self.key_file, 'rb') as f:
                return f.read().strip()

        raise RepairableException(
            f"Master encryption key not found. Set {self.master_key_env} environment variable "
            f"or provide key file at {self.key_file}"
        )

    def get_secrets(self) -> Dict[str, str]:
        """Decrypt and parse secrets file."""
        try:
            encrypted_data = read_file(self.encrypted_file, mode='rb')
        except Exception:
            # No encrypted file exists yet
            return {}

        if len(encrypted_data) < self._salt_size + self._nonce_size:
            raise RepairableException("Invalid encrypted secrets file format")

        salt = encrypted_data[:self._salt_size]
        nonce = encrypted_data[self._salt_size:self._salt_size + self._nonce_size]
        ciphertext = encrypted_data[self._salt_size + self._nonce_size:]

        master_password = self._get_master_password()
        key = self._derive_key(master_password, salt)

        aesgcm = AESGCM(key)
        try:
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        except Exception as e:
            raise RepairableException(f"Failed to decrypt secrets: {e}")

        # Parse as JSON
        try:
            secrets_json = json.loads(plaintext.decode('utf-8'))
            return {k.upper(): str(v) for k, v in secrets_json.items()}
        except Exception as e:
            raise RepairableException(f"Invalid secrets format: {e}")

    def save_secrets(self, secrets: Dict[str, str]) -> None:
        """Encrypt and save secrets."""
        # Convert to JSON
        secrets_json = {k.upper(): str(v) for k, v in secrets.items()}
        plaintext = json.dumps(secrets_json, indent=2).encode('utf-8')

        # Generate salt and nonce
        salt = py_secrets.token_bytes(self._salt_size)
        nonce = py_secrets.token_bytes(self._nonce_size)

        master_password = self._get_master_password()
        key = self._derive_key(master_password, salt)

        aesgcm = AESGCM(key)
        ciphertext = aesgcm.encrypt(nonce, plaintext, None)

        # Write salt + nonce + ciphertext
        encrypted_data = salt + nonce + ciphertext
        write_file(self.encrypted_file, encrypted_data, mode='wb')

    def get_available_keys(self) -> List[str]:
        return list(self.get_secrets().keys())

    @property
    def backend_name(self) -> str:
        return "encrypted_file"


class DockerSecretsBackend(SecretBackend):
    """Docker secrets backend - reads each secret from /run/secrets/ directory.

    In Docker Swarm mode, secrets are mounted as files in /run/secrets/.
    Each secret name corresponds to a file. Secret values are the file contents.
    """

    def __init__(self, secrets_dir: str = "/run/secrets"):
        self.secrets_dir = Path(secrets_dir)

    def get_secrets(self) -> Dict[str, str]:
        """Read all secrets from /run/secrets/ directory."""
        secrets = {}
        if not self.secrets_dir.exists():
            return secrets

        for secret_file in self.secrets_dir.iterdir():
            if secret_file.is_file():
                try:
                    value = secret_file.read_text().strip()
                    key = secret_file.name.upper()
                    secrets[key] = value
                except Exception:
                    # Skip unreadable secrets
                    continue

        return secrets

    def save_secrets(self, secrets: Dict[str, str]) -> None:
        """Docker secrets backend is read-only for runtime.
        Secrets must be managed via Docker swarm commands.
        """
        raise RepairableException(
            "Docker secrets backend does not support saving at runtime. "
            "Use 'docker secret create/update' commands to manage secrets."
        )

    def get_available_keys(self) -> List[str]:
        return [f.name.upper() for f in self.secrets_dir.iterdir() if f.is_file()]

    @property
    def backend_name(self) -> str:
        return "docker_secrets"


class KeyringBackend(SecretBackend):
    """OS keyring backend - uses system credential storage."""

    def __init__(self, service_name: str = "agent-zero"):
        self.service_name = service_name
        try:
            import keyring
            self.keyring = keyring
        except ImportError:
            raise RepairableException(
                "keyring library not installed. Install with: pip install keyring"
            )

    def get_secrets(self) -> Dict[str, str]:
        """Load all secrets from keyring."""
        secrets = {}
        # keyring doesn't have a standard way to list all keys
        # We rely on a stored list or known keys
        # For simplicity, we'll store a master index key
        index_key = f"{self.service_name}:__index__"
        index_json = self.keyring.get_password(self.service_name, index_key)
        if index_json:
            try:
                keys = json.loads(index_json)
                for key in keys:
                    value = self.keyring.get_password(self.service_name, key)
                    if value:
                        secrets[key] = value
            except Exception:
                pass
        return secrets

    def save_secrets(self, secrets: Dict[str, str]) -> None:
        """Save all secrets to keyring."""
        # Store each secret
        for key, value in secrets.items():
            self.keyring.set_password(self.service_name, key, value)

        # Update index
        index_key = f"{self.service_name}:__index__"
        self.keyring.set_password(self.service_name, index_key, json.dumps(list(secrets.keys())))

    def get_available_keys(self) -> List[str]:
        """List keys from index."""
        index_key = f"{self.service_name}:__index__"
        index_json = self.keyring.get_password(self.service_name, index_key)
        if index_json:
            try:
                return json.loads(index_json)
            except Exception:
                pass
        return []

    @property
    def backend_name(self) -> str:
        return "keyring"


def get_secret_backend(backend_name: str, **kwargs) -> SecretBackend:
    """Factory function to create backend instance."""
    backends = {
        'plaintext': PlaintextBackend,
        'encrypted_file': EncryptedFileBackend,
        'docker_secrets': DockerSecretsBackend,
        'keyring': KeyringBackend,
    }

    backend_class = backends.get(backend_name)
    if not backend_class:
        raise ValueError(f"Unknown secret backend: {backend_name}. Available: {list(backends.keys())}")

    return backend_class(**kwargs)
