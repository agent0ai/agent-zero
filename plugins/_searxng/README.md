# SearXNG

The `web-search` skill runs `python -m plugins._searxng.search 'query'` from the Agent Zero repository root in the local terminal. `--status` reports progress without waiting or starting a sandbox. Stdout is JSON (up to ten results and unavailable engines); setup/wait notices go to stderr. No dedicated search tool is registered.

First use creates `service-searxng` through the shared `helpers.sandbox` Python/CLI API and installs pinned SearXNG into the image's existing Python. No additional interpreter, virtual environment, compiler or outer SearXNG installation is needed. Shared dependency constraints apply. The guest calls Flask's WSGI search endpoint directly, with no HTTP listener or Valkey server.

Concurrent CLI processes share a lock covering creation, installation, query and shutdown. Waiting calls report the current status, then reuse the completed installation. The success fingerprint is written atomically only after installation and `pip check`. Failures or killed callers release the process lock; status detects interrupted work and the next query retries. Disable/uninstall use the same lock. Status does not store queries.

Each call stops its child sandbox and retains installed files; persist `/a0/usr` across container replacements. Existing worker sandboxes are reused with updated command/mounts. Settings keep JSON search and exclude radio browser, Wikidata and Tor engines. VPS addresses can encounter upstream CAPTCHA, 403 or rate limits even when SearXNG is healthy.

Run `pytest tests/test_searxng_plugin.py tests/test_search_cli.py`. Live verification additionally needs a disposable container with simultaneous first-use requests, status polling, retry, warm reuse and image-Python checks.
