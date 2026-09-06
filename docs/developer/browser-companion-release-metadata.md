# Chrome Browser Bridge setup and releases

## Install and pair once

The Chrome Web Store item is still a draft. The extension's supplied unpacked
ZIP contains an offline `START-HERE.html` guide and ready-to-load `extension`
folder. No source build is required. Keep that folder at a permanent location,
then use Chrome → Extensions → Developer mode → Load unpacked. The production
identity is `nhliclifilepdkoolioacpjpijomfplj`; Chrome's Developer mode switch
does not select a development trust channel. The old development endpoints and
limited runtime are retired; old credentials and saved site grants are not
converted or deleted. Existing development selections stop without fallback and
require explicit production pairing and selection.

Install the native companion on the computer running Chrome, not in Docker or
WSL. macOS 13+ has a signed/notarized 2.12.3 installer for Intel and Apple Silicon.
Windows and Linux can load the extension, but their production native installers
remain incomplete. [Current user setup guide](https://github.com/TerminallyLazy/agent-zero-browser-support/blob/main/SETUP.md).

After installation, create a five-minute code in Browser settings, enter the
WebUI address and code in extension Options, and select this browser as Agent
Zero's default. The default applies across chats without replacing explicit
project choices. Pairing survives ordinary updates and panel closure. Runtime
readiness additionally requires signed release admission and reconciliation.
Remembered-site or explicitly enabled All websites access avoids repeated site
prompts; consequential actions still require separate approval.

## Operator activation policy

Pairing requires `A0_BROWSER_BRIDGE_ROLLOUT=preview|available` and
`A0_BROWSER_BRIDGE_EXTENSION_ID` set to the exact production ID. An optional
`A0_BROWSER_BRIDGE_SERVER_BASE_URL` pins the canonical external URL; only HTTPS
or loopback HTTP is supported. Preserve normal WebUI authentication and CSRF.

`A0_BROWSER_BRIDGE_RELEASE_POLICY_FILE` must identify an operator-provisioned
publisher-signed policy. Core rechecks its signature, expiry, and exact extension
ID/version plus companion version/platform/architecture on admission. Extension
0.1.1 needs new exact entries for companion 2.12.3 on Darwin aarch64 and x86_64;
the old 0.1.0 entries do not admit it. Preserve reviewed existing entries when
issuing an update. Never edit signed JSON by hand, auto-accept a higher version,
use a fixture key, or add unreleased Windows/Linux tuples. This policy is distinct
from the installer catalog and the presentation metadata below. Its maximum
lifetime is 90 days and it requires publisher renewal before expiry.

The source-adjacent `_a0_connector` and `_browser` DOX contracts own endpoint
schemas and runtime authority. Old foundation-only/hello-only descriptions no
longer describe the composed production runtime.

## Installer metadata API

Agent Zero exposes a read-only installer metadata endpoint:

```text
POST /api/plugins/_a0_connector/v1/browser_companion_release
```

The endpoint requires the normal authenticated WebUI session and CSRF token. It accepts only an empty JSON object. It does not download, execute, or install anything.

Connector capability discovery advertises `browser_companion_release_metadata` when the endpoint and its helper are present. That flag reports API-contract availability only; it does not mean that a release, installer, companion, pairing flow, or browser runtime is ready.

## Docker boundary

The native companion belongs on the computer running Chrome or another supported Chromium-family browser. It is never installed in the Agent Zero Docker container: a container cannot register a native-messaging host in the user's desktop browser merely by writing its own filesystem.

Browser settings can use this endpoint to present pinned OS-specific downloads. The user downloads and runs the wrapper on the browser host. Pairing begins only after that host installation verifies locally.

## Server-pinned metadata

This foundation remains unavailable unless the Agent Zero server operator configures all three values:

- `A0_BROWSER_COMPANION_CATALOG_URL`: an immutable HTTPS catalog URL without credentials, query, or fragment;
- `A0_BROWSER_COMPANION_CATALOG_KEY_FINGERPRINT`: `sha256:` followed by the pinned release-root fingerprint;
- `A0_BROWSER_COMPANION_RELEASE_METADATA`: a bounded JSON object containing the stable release, detached catalog-signature URL, protocol/trust ranges, minimum secure companion version, release key ID, and complete artifact matrix.

Schema v1 requires the complete macOS/Windows/Linux matrix. Schema v2 adds a
nonempty, sorted, unique `platforms` list and requires complete delivery groups
only for those platforms. A Mac-only v2 release must not imply Windows/Linux
availability. Each artifact has an immutable HTTPS URL, exact filename,
SHA-256 digest, and byte size.

`A0_BROWSER_COMPANION_RELEASE_METADATA` is a strict WebUI presentation envelope,
not the signed catalog. Top-level v1 keys are `schema_version`, `release`,
`channel`, `published_at`, `protocol`, `trust`, `minimum_secure_companion`,
`catalog_signature_url`, `release_key_id`, and `artifacts`; v2 additionally
requires `platforms`. Every artifact has exactly `name`, `platform`, `arch`,
`kind`, `download_url`, `sha256`, and `size`. Unknown or duplicate fields fail
closed. Catalog-only origins and native registration data are not projected.

The release pipeline—not browser page content—owns these values. The endpoint rejects request-supplied URLs, paths, extension IDs, or metadata overrides. Responses never contain signing/private keys, Agent Zero credentials, native paths, raw environment data, or exception text.

Missing, invalid, incomplete, below-floor, or protocol-incompatible configuration returns `state: unavailable` with empty artifact data. A usable presentation returns the distinct `a0.browser-bridge.release-metadata.v1` contract with `state: available`, references the install contract separately, and always includes `install_ready: false`. Available means only that the pinned public presentation metadata is syntactically complete and compatible with this server. Core's compiled minimum secure companion is `2.12.0`; supplied metadata may raise the effective floor but cannot lower it. Agent Zero Core does not fetch or cryptographically verify the catalog or artifact bytes at this endpoint. The browser-host installer or CLI treats this projection as unverified, fetches the catalog and detached signature, verifies them against its independently pinned public root, and requires the signed catalog to match the selected artifact's name, platform, architecture, kind, download URL, digest, and size. It then verifies the artifact digest, platform signature, and self-test before execution. The host companion, browser registration, extension, and pairing remain unchecked.

Catalog, signature, and artifact URLs are bounded canonical HTTPS URLs. Raw or percent-decoded controls, backslashes, credentials, query/fragment delimiters, ambiguous hostnames, double-leading path separators, dot segments, and artifact filename mismatches fail closed.
