# File Browser connection control

Authenticated, CSRF-protected actions manage provider discovery, saved connections, connection tests, mutations and Editor sessions. Delegate provider/root/permission logic to `helpers.file_connections`, with blocking calls in a worker thread. Keep public validation errors and filtered transport failures; never return secrets.

File bodies use the common multipart upload and prepared download routes. This endpoint has no base64 upload or in-memory download/archive actions. Editor text remains a bounded text payload by design.
