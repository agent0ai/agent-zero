# File Browser Connections API

`FileBrowserConnections` handles authenticated, CSRF-protected remote connection operations. The endpoint retains `ApiHandler` defaults. `dispatch` delegates to `helpers.file_connections` in a worker thread; no protocol implementation belongs here.

Actions: list providers and redacted saved connections; save/remove/test a connection; bounded upload/download/archive; mkdir/rename/delete; shared Editor operations. Protocol-specific setup uses each plugin's own APIs. Requests identify the provider and connection or use `/@connections/<provider>/<id>/...` paths. Legacy `/@ssh/<id>/...` paths resolve through the SSH provider.

Secrets are never returned. Provider exceptions are filtered; public validation errors describe recovery, transport errors use a generic message. Download results use the existing stream response. Editor mutations are serialized with the service lock. Test with `tests/test_file_connections.py` and each community plugin's transport check in the framework runtime.

Upload base64 admission and decoded bytes use the current FileBrowser transfer limit. Downloads and aggregate ZIP contents use the same setting; Editor operations use their independent editing limit.
