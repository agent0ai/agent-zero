# Legacy Tunnel Endpoint

Compatibility entry for the Remote Control plugin's API. Requests delegate to `plugins._tunnel.api.tunnel` and retain normal route authentication and CSRF protection. There is no separate tunnel API port or in-process provider fallback.

The plugin owns create/stop/get/notifications/verify behavior and sandbox state. Verify with tunnel plugin/provider tests, origin security tests, and a real authenticated HTTP request.
