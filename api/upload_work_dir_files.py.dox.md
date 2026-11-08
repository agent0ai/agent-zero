# Files uploads

Authenticated, CSRF-protected multipart uploads accept `files[]` and `path`. Delegate local/remote streaming, size enforcement, and atomic writes to FileBrowser; do not inspect a private size checker or duplicate policy in this endpoint. The endpoint maps plain `FileLimitExceeded` to a 413 response without changing ApiHandler. Successful changes still emit `workdir_file_mutation_after` and refresh the listing.

Blocking file/provider I/O runs in a worker thread in both development and production, with no base64 roundtrip. The async `upload_file` base64 entry point remains available for compatibility. Failed local writes preserve existing files; partial batch failures retain the successful/failed filename response fields.

Verify multipart boundaries, atomic preservation, remote provider uploads and mutation notifications.
