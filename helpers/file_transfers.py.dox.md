# Shared file transfers

`copy_stream`/`TransferWriter` count actual bytes in bounded chunks, handle short writes, and return size/SHA-256. The operation owner supplies the limit; this module does not read settings. `FileLimitExceeded` is a plain `ValueError`; HTTP response choices belong to individual endpoints. Missing download tokens raise `FileNotFoundError`, and denied delivery raises `PermissionError`.

`write_stream_atomic(source, target, max_bytes=...)` accepts a binary stream and stages beside the destination, preserves existing mode/ownership, detects concurrent destination changes and atomically publishes; new names publish exclusively. Failure removes staging and preserves existing data. Links and nonregular destinations are rejected.

`stream_file_download` hashes and serves the same open descriptor, counts bytes before headers, closes on completion/interruption, and owns requested temporary-file cleanup. POSIX temporary files are unlinked as soon as opened so process exit also releases them. Generic downloads do not acquire a Files policy implicitly.

Prepared responses use random, single-use, authenticated-route tokens. Unclaimed responses expire after two minutes and close their descriptors; claiming cancels expiry, so download duration is not limited. A supplied authorization callback rechecks remote access immediately before delivery. Tokens are process-local, matching the single-process UI server and Connector transfer state.

Verify atomic failure/mode preservation, live-byte limits, held-descriptor downloads, token reuse/revocation and temporary cleanup with `tests/test_file_transfer_safety.py`.
