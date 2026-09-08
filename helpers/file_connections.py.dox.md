# File Connections

Local and remote Editor paths inherit FileBrowser's text size, binary and UTF-8 rules. The transfer ceiling also comes from FileBrowser; do not introduce separate Editor constants here.

Live providers may implement `connections()` instead of persisted configuration. Their metadata marks them managed; save/remove are rejected, and records are refreshed on each lookup so disconnected hosts cannot be used. Underscore-prefixed internal fields never enter public connection responses. The bundled Connector provider supplies CLI and Launcher folders through this seam.

Version 1 of the shared Files connection interface. `providers()` calls the enabled-plugin `file_browser_providers` extension with a mutable `providers` dictionary. Each plugin registers a uniquely named extension file and a provider keyed by ID. Disabling a plugin removes its connections from discovery and rejects subsequent operations.

Providers own `id`, `plugin_name`, `title`, `fields`, `validate(config)`, and context-managed `open(config, data_directory)`. Fields describe labels/defaults/types, secret or hidden values, and dependent-field resets. Optional `permissions` limits supported actions. Protocol-specific setup belongs in plugin APIs and WebUI extensions, not the core service. Adapters expose list/stat/read/write/mkdir/rename/remove; read returns bytes plus a revision, and write uses that revision for conflict detection. New writes must refuse an existing target. Providers document protocol-specific concurrency limits.

`listing_config`, `save_connection`, and `remove_connection` own private per-plugin `data/connections.json` (0600, atomic replacement). Secret fields are omitted from responses, with boolean `savedSecrets` indicators. An omitted secret preserves it; an explicit empty value clears it. Optional legacy records migrate once without deleting originals. Private keys remain provider-owned and are never returned.

Remote paths use `/@connections/<provider>/<32hex-id>/<relative>`. Legacy SSH paths are accepted. Permission checks apply to every operation, including archives and Editor sessions. Root mutation, traversal, cross-connection moves, and self-nesting moves are rejected. Links are excluded from listings and archives. Archives use the configured transfer limit on aggregate uncompressed bytes, with 1000 entries and depth 64. Editor writes use the independent text limit. Editor: UTF-8, nonbinary, shared configurable text limit (10 MiB by default), at most 256 in-process sessions. Connection configuration changes invalidate affected sessions.

These permissions constrain Files, not arbitrary agent tools or server accounts. Transport authentication, encryption, root semantics and filesystem concurrency guarantees belong to adapters. Verify with `tests/test_file_connections.py` and plugin transport tests; live UI covers discovery, settings, file selection and Editor handoff.
