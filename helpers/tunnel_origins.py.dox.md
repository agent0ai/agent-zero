# Tunnel Origin Discovery

`origin_from_url` and `origin_key` normalize origins and default ports for HTTP CSRF and WebSocket checks. Invalid values return None.

`get_active_tunnel_origins()` reads the Remote Control plugin's bounded, briefly cached status. It never starts a sandbox or queries a secondary HTTP controller; stopped/disabled/unavailable plugins contribute no origin. Keep normal origin validation intact.

Verify with `tests/test_csrf_tunnel_origins.py` and `tests/test_ws_csrf.py`.
