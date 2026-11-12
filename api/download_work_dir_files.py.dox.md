# Files downloads

Authenticated, CSRF-protected POST accepts `paths` and optional `currentPath`. Shared FileBrowser helpers select local/remote storage, enforce operation policy and prepare a streamed response. Return a download URL and filename; the browser follows it natively without loading a file into a JavaScript Blob.

Authenticated GET claims the opaque single-use token. Unclaimed responses expire after two minutes; remote permissions are rechecked at claim. This endpoint does not select byte limits. File/ZIP work runs outside the request event loop. The existing development RFC adapter remains separate from production HTTP streaming.

Verify preparation errors, token auth/CSRF, one-time delivery, limits and response cleanup. Generic Connector downloads use `download_work_dir_file` instead.

This endpoint maps plain size, missing-token and permission exceptions to explicit 413/404/403 responses. Framework-wide exception and malformed-JSON behavior is unchanged.

Development RFC reads use `files.read_file_base64` directly, without importing another endpoint.
