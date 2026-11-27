# Purpose

Bundle Tuxee's noVNC 1.6.0 source client for Browser without external runtime imports.

# Ownership

Matched core/vendor source modules from Tuxee; `../../vnc.js` owns A0 integration.
`NOVNC-*` files preserve noVNC/MPL/BSD/pako notices.

# Local Contracts

Keep upstream modules together. Retain Tuxee's two fixes: `core/rfb.js` rejects
invalid remote framebuffer dimensions; `core/util/browser.js` closes the H.264
probe's VideoFrame and decoder on success and failure. Never vendor node_modules.
Upstream tag archive SHA-256: `5066103959ef4e9b10f37e5a148627360dd8414e4cf8a7db92bdbd022e728aaa`.

# Work Guidance

Update the matched sources, fixes and license notices together with Tuxee.

# Verification

Run the Browser viewer integration check and `tests/test_browser_vnc.py`.

# Child DOX Index

No children.
