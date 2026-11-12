# Browser setup UI

Production setup uses the read-only setup API, never client-built download URLs or runtime flags. Validate the exact projection, configured production extension URL, bounded installer list and canonical HTTPS URLs before rendering links. The projection is server-configured presentation metadata, not a signature/install/runtime proof. The browser-host installer is responsible for cryptographic verification.

Use the visiting browser's platform as a suggestion, never the Linux Docker server's OS. Allow explicit macOS, Windows and Linux selection and unknown OS. Missing OS artifacts remain unavailable with no substitute installer. Windows architecture is explicit because browser platform strings cannot reliably identify emulated hardware.

Mount/cleanup fence asynchronous replies. Refresh never downloads, pairs, changes chat selection or grants site permission. Keep setup one-time guidance separate from authoritative current-chat runtime status and existing paired inventory. A stored pair does not prove full control, nor does losing a connection require a new pair.
