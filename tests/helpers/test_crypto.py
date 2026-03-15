"""Tests for python/helpers/crypto.py — encryption/hashing."""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# --- hash_data ---


class TestHashData:
    def test_produces_hex_digest(self):
        from python.helpers.crypto import hash_data

        result = hash_data("hello", "password")
        assert isinstance(result, str)
        assert len(result) == 64  # SHA256 hex = 64 chars
        assert all(c in "0123456789abcdef" for c in result)

    def test_deterministic(self):
        from python.helpers.crypto import hash_data

        r1 = hash_data("data", "secret")
        r2 = hash_data("data", "secret")
        assert r1 == r2

    def test_different_data_different_hash(self):
        from python.helpers.crypto import hash_data

        r1 = hash_data("data1", "secret")
        r2 = hash_data("data2", "secret")
        assert r1 != r2

    def test_different_password_different_hash(self):
        from python.helpers.crypto import hash_data

        r1 = hash_data("data", "pass1")
        r2 = hash_data("data", "pass2")
        assert r1 != r2

    def test_empty_strings(self):
        from python.helpers.crypto import hash_data

        result = hash_data("", "")
        assert isinstance(result, str)
        assert len(result) == 64


# --- verify_data ---


class TestVerifyData:
    def test_verifies_correct_hash(self):
        from python.helpers.crypto import hash_data, verify_data

        data, password = "payload", "secret"
        h = hash_data(data, password)
        assert verify_data(data, h, password) is True

    def test_rejects_wrong_data(self):
        from python.helpers.crypto import hash_data, verify_data

        h = hash_data("original", "secret")
        assert verify_data("tampered", h, "secret") is False

    def test_rejects_wrong_password(self):
        from python.helpers.crypto import hash_data, verify_data

        h = hash_data("data", "correct")
        assert verify_data("data", h, "wrong") is False

    def test_rejects_wrong_hash(self):
        from python.helpers.crypto import verify_data

        assert verify_data("data", "0" * 64, "secret") is False


# --- encrypt_data / decrypt_data ---


class TestEncryptDecrypt:
    def test_encrypt_decrypt_roundtrip(self):
        from python.helpers.crypto import (
            _generate_private_key,
            _generate_public_key,
            encrypt_data,
            decrypt_data,
        )

        priv = _generate_private_key()
        pub_hex = _generate_public_key(priv)
        plain = "sensitive data"
        encrypted = encrypt_data(plain, pub_hex)
        decrypted = decrypt_data(encrypted, priv)
        assert decrypted == plain

    def test_encrypted_is_hex_string(self):
        from python.helpers.crypto import _generate_private_key, _generate_public_key, encrypt_data

        priv = _generate_private_key()
        pub_hex = _generate_public_key(priv)
        encrypted = encrypt_data("test", pub_hex)
        assert isinstance(encrypted, str)
        assert all(c in "0123456789abcdef" for c in encrypted)

    def test_different_plaintexts_produce_different_ciphertexts(self):
        from python.helpers.crypto import _generate_private_key, _generate_public_key, encrypt_data

        priv = _generate_private_key()
        pub_hex = _generate_public_key(priv)
        c1 = encrypt_data("a", pub_hex)
        c2 = encrypt_data("b", pub_hex)
        assert c1 != c2

    def test_unicode_roundtrip(self):
        from python.helpers.crypto import (
            _generate_private_key,
            _generate_public_key,
            encrypt_data,
            decrypt_data,
        )

        priv = _generate_private_key()
        pub_hex = _generate_public_key(priv)
        plain = "café 日本語 🎉"
        encrypted = encrypt_data(plain, pub_hex)
        decrypted = decrypt_data(encrypted, priv)
        assert decrypted == plain

    def test_empty_string_roundtrip(self):
        from python.helpers.crypto import (
            _generate_private_key,
            _generate_public_key,
            encrypt_data,
            decrypt_data,
        )

        priv = _generate_private_key()
        pub_hex = _generate_public_key(priv)
        encrypted = encrypt_data("", pub_hex)
        decrypted = decrypt_data(encrypted, priv)
        assert decrypted == ""


# --- _generate_private_key ---


class TestGeneratePrivateKey:
    def test_returns_rsa_key(self):
        from python.helpers.crypto import _generate_private_key
        from cryptography.hazmat.primitives.asymmetric import rsa

        key = _generate_private_key()
        assert isinstance(key, rsa.RSAPrivateKey)

    def test_key_size_2048(self):
        from python.helpers.crypto import _generate_private_key

        key = _generate_private_key()
        assert key.key_size == 2048

    def test_generates_different_keys_each_time(self):
        from python.helpers.crypto import _generate_private_key, _generate_public_key

        k1 = _generate_private_key()
        k2 = _generate_private_key()
        pub1 = _generate_public_key(k1)
        pub2 = _generate_public_key(k2)
        assert pub1 != pub2


# --- _generate_public_key ---


class TestGeneratePublicKey:
    def test_returns_hex_string(self):
        from python.helpers.crypto import _generate_private_key, _generate_public_key

        priv = _generate_private_key()
        pub = _generate_public_key(priv)
        assert isinstance(pub, str)
        assert all(c in "0123456789abcdef" for c in pub)

    def test_can_be_decoded_back(self):
        from python.helpers.crypto import (
            _generate_private_key,
            _generate_public_key,
            _decode_public_key,
        )

        priv = _generate_private_key()
        pub_hex = _generate_public_key(priv)
        decoded = _decode_public_key(pub_hex)
        assert decoded is not None


# --- _decode_public_key ---


class TestDecodePublicKey:
    def test_decodes_valid_hex_to_rsa_key(self):
        from python.helpers.crypto import (
            _generate_private_key,
            _generate_public_key,
            _decode_public_key,
        )
        from cryptography.hazmat.primitives.asymmetric import rsa

        priv = _generate_private_key()
        pub_hex = _generate_public_key(priv)
        key = _decode_public_key(pub_hex)
        assert isinstance(key, rsa.RSAPublicKey)

    def test_raises_for_invalid_key_type(self):
        from python.helpers.crypto import _decode_public_key
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import ed25519

        # Create an Ed25519 key and encode as hex (not RSA)
        priv = ed25519.Ed25519PrivateKey.generate()
        pub = priv.public_key()
        pem = pub.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        hex_str = pem.hex()
        with pytest.raises(TypeError, match="not an RSAPublicKey"):
            _decode_public_key(hex_str)

    def test_raises_for_invalid_hex(self):
        from python.helpers.crypto import _decode_public_key

        with pytest.raises(ValueError):
            _decode_public_key("not-valid-hex!!")


# --- Integration: full flow ---


class TestCryptoIntegration:
    def test_hash_verify_workflow(self):
        from python.helpers.crypto import hash_data, verify_data

        data = "user:123:token"
        password = "hmac-secret"
        h = hash_data(data, password)
        assert verify_data(data, h, password) is True
        assert verify_data(data + "x", h, password) is False

    def test_encrypt_decrypt_workflow_with_generated_keys(self):
        from python.helpers.crypto import (
            _generate_private_key,
            _generate_public_key,
            encrypt_data,
            decrypt_data,
        )

        priv = _generate_private_key()
        pub_hex = _generate_public_key(priv)
        messages = ["short", "a" * 100, "multi\nline\ncontent"]
        for msg in messages:
            enc = encrypt_data(msg, pub_hex)
            dec = decrypt_data(enc, priv)
            assert dec == msg
