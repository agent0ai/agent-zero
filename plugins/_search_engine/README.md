# Web Search

The `web-search` skill teaches agents to run the [SearXNG query CLI](../_searxng/README.md) in the local terminal. First use installs search dependencies in a private sandbox; concurrent calls wait and can inspect setup status. Results are JSON with up to ten titles, URLs and snippets, plus upstream engine failures.

There is no `search_engine` agent tool. WebUI handlers remain for displaying saved search-tool messages.
