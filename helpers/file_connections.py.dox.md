# Remote Files providers

Enabled plugins register providers through `file_browser_providers`. Core owns saved connection permissions, redacted metadata, root-relative paths, staging, limits, Editor sessions and filtered provider errors. Container root access and a provider root are different trust boundaries. Reject traversal, root mutation, cross-connection moves and stale/disabled connections.

All five new plugins and the bundled host provider share one stream interface, without legacy fallbacks: `read(relative, destination, limit)` writes bounded chunks and returns a revision; `write(relative, source, expected=None)` consumes a seekable staged stream and returns the new revision. A `None` destination can discard streamed data for conflict hashing. Files transfers use file-backed staging, not bytes/base64. Only the Editor convenience methods materialize bounded UTF-8 text.

Reads and delivery recheck connection permissions. Writes stage/count bytes before handing a stream to the provider. Archive creation counts aggregate uncompressed bytes and entries, cleans up on failure, and returns an owned file stream. Provider transport failures become filtered `ValueError` messages; declared public validation messages remain actionable. Protocol-specific code belongs in its plugin.

Verify provider permissions, streaming limits, conflicts and revocation with `tests/test_file_connections.py`, shared safety tests and each plugin's transport tests.

Saved connections are read with `files.read_file_json` from the provider data directory. New providers have no automatic prototype-state migration; managed host providers continue supplying their live connections directly.
