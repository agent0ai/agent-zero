# crypto.py DOX

## Purpose

- Own the `crypto.py` helper module.
- This module hashes, verifies, encrypts, and decrypts data for signed or protected payloads.
- Keep this file-level DOX profile synchronized with `crypto.py` because this directory is intentionally flat.

## Ownership

- `crypto.py` owns the runtime implementation.
- `crypto.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Top-level functions:
- `hash_data(data: str, password: str)`
- `verify_data(data: str, hash: str, password: str)`
- `_generate_private_key()`
- `_generate_public_key(private_key: rsa.RSAPrivateKey)`
- `_decode_public_key(public_key: str) -> rsa.RSAPublicKey`
- `encrypt_data(data: str, public_key_pem: str)`
- `_encrypt_data(data: bytes, public_key: rsa.RSAPublicKey)`
- `decrypt_data(data: str, private_key: rsa.RSAPrivateKey)`

## Runtime Contracts

- Helper modules own reusable framework APIs and must preserve public callers unless all callers, tests, and docs are updated together.
- Update this file whenever public functions, classes, persistence behavior, path/security assumptions, side effects, or cross-module contracts change.
- Observed side-effect areas: secret handling.
- Imported dependency areas include: `cryptography.hazmat.primitives`, `cryptography.hazmat.primitives.asymmetric`, `hashlib`, `hmac`, `os`.

## Key Concepts

- Important called helpers/classes observed in the source: `hmac.new.hexdigest`, `rsa.generate_private_key`, `private_key.public_key.public_bytes.hex`, `bytes.fromhex`, `serialization.load_pem_public_key`, `_encrypt_data`, `public_key.encrypt`, `b.hex`, `private_key.decrypt`, `b.decode`, `hash_data`, `TypeError`, `data.encode`, `_decode_public_key`, `padding.OAEP`, `hmac.new`, `private_key.public_key.public_bytes`, `password.encode`, `padding.MGF1`, `hashes.SHA256`.
- Keep request/response, tool, or helper semantics documented here at the same time as source changes.

## Work Guidance

- Preserve public helper APIs used by core code and plugins unless every caller is updated.
- Keep path, auth, secret, persistence, network, and subprocess behavior explicit and bounded.
- Prefer adding cohesive helper functions here only when behavior is reused across modules.

## Verification

- Run targeted tests for changed helper behavior; run security regressions for auth, filesystem, WebSocket, tunnel, upload, or secret-handling helpers.
- No direct test reference was found by name search; choose the nearest behavioral test or perform a focused smoke check.

## Child DOX Index

No child DOX files.
