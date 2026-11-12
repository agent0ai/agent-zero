# Browser Companion Release Metadata API

## Purpose

- Expose configured, non-secret Browser companion presentation metadata to an authenticated WebUI session. This endpoint does not establish cryptographic pinning.
- Keep Docker/WebUI delivery separate from installation on the user's browser host.

## Request and response

- Route: `POST /api/plugins/_a0_connector/v1/browser_companion_release`.
- Request body: empty JSON object only. Request-supplied URLs, paths, extension IDs, artifacts, or overrides are rejected.
- Response contract: `a0.browser-bridge.release-metadata.v1`, schema version 1. It references `a0.browser-bridge.install.v1` separately and always reports `install_ready: false`.
- Capability discovery name: `browser_companion_release_metadata`. Its presence means only that this endpoint contract exists; it does not advertise a configured release, installer, pairing, or browser runtime.
- An `available` response contains only allowlisted public catalog, compatibility, release, digest, size, target, and download metadata. Available means that the configured presentation metadata passed bounded shape, canonical URL, complete-matrix, and server-compatibility checks; it never means installation is ready. Agent Zero Core has not verified the detached catalog signature or artifact bytes.
- Missing, invalid, incomplete, or incompatible server metadata returns `state: unavailable` with no catalog, release, or artifacts.
- Input presentation schema 1 keeps the exact nine-artifact matrix and rejects a
  `platforms` field. Input schema 2 requires a nonempty, sorted, unique list of
  known `linux`, `macos`, `windows` platforms and the exact union of complete
  artifact groups for those platforms. No omitted-platform artifact, duplicate,
  partial group or placeholder is accepted. The public response remains schema
  1 of the existing presentation contract; neither input is a signed catalog or
  proves cryptographic verification. This lets a genuine Mac-only release be
  presented without claiming Windows/Linux artifacts exist.

## Security and side effects

- Uses `ApiHandler` directly because this is a same-origin WebUI endpoint: session authentication and CSRF protection are both required. `ProtectedConnectorApiHandler` is intentionally not used because it disables CSRF for connector-client routes; API-key and loopback overrides are not added. Nonempty malformed JSON is rejected from raw request bytes even when the generic API parser supplied an empty dictionary.
- Reads only the three documented server environment values through the companion-release helper.
- Treats the configured release JSON as a strict presentation envelope, not as the signed release catalog. It intentionally excludes catalog-only extension origins and other native registration data.
- Enforces the compiled server floor `2.12.0` independently of supplied metadata; metadata may raise the effective floor but cannot lower it.
- Never returns raw environment data, private/signing keys, server credentials, extension IDs, native-host paths, user paths, or exception text.
- Performs no download, install, filesystem write, subprocess, Docker mutation, pairing, or browser operation.
- Every response states that delivery targets the user's browser host and that Docker installation is unsupported.
- Every response states that the browser-host installer/CLI must verify the detached catalog signature against its own pinned public root and verify the selected artifact before execution.

## Verification

- Run `pytest tests/test_browser_companion_release_metadata.py`.
- Keep invalid-field, secret-sentinel, compatibility, complete-artifact-matrix, request-body rejection, and authentication/CSRF contract assertions green.
