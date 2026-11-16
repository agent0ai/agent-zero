# SearXNG

Web search runs in its own `service-searxng` sandbox. The first search installs dependencies automatically and shows a notice in the search tool log; setup may take several minutes. Later calls reuse the installation. The worker stops after two idle minutes and starts again on demand.

The installer fetches a pinned SearXNG revision (see `sandbox/install.sh`) and installs it into the sandbox image's existing Python. Bootstrap packages are declared in `sandbox/requirements.txt`; SearXNG supplies its own runtime requirements. Shared worker security constraints apply to both. No additional Python runtime, virtual environment, compiler or outer-image SearXNG installation is required.

The guest calls SearXNG's Flask/WSGI search endpoint directly and returns JSON through the shared private worker transport. There is no HTTP listener, exposed port, Supervisor service or Valkey server requirement. `sandbox/settings.yml` enables JSON results and retains the original general-search defaults, with radio browser, Wikidata and Tor engines excluded. The worker generates its own secret at startup.

`_search_engine` formats up to ten results and reports failures or unavailable engines when there are no results. VPS addresses may encounter upstream rate limits, CAPTCHAs or 403 responses even when SearXNG is working correctly.

Disabling stops the worker; uninstalling deletes its sandbox. Installer changes trigger provisioning again on the next start. Persist `/a0/usr` to retain sandbox installations across container replacements.

Verification: `pytest tests/test_searxng_plugin.py tests/test_search_engine_tool.py tests/test_sandbox_workers.py`. Also exercise first-use and warm searches in a fresh Docker container; ordinary tests do not contact external engines.
