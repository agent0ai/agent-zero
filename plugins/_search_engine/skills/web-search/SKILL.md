---
name: web-search
description: "Search the web for current facts, sources and links using sandboxed SearXNG."
triggers:
  - "search the web"
  - "find online"
  - "latest news"
  - "web research"
---

# Web Search

Run the [search CLI](../../../_searxng/search.py) in Agent Zero's **local** terminal (the outer container), using `code_execution_tool` with `runtime: "terminal"` and `destination: "local"`:

```bash
cd /a0 && python -m plugins._searxng.search 'your search query'
```

For a source installation, use its repository root instead of `/a0`.

The first query creates the sandbox and installs SearXNG in the image's existing Python. Tell the user this may take a little while. Keep the terminal session and collect its output if the call returns before setup finishes; do not launch another copy just to poll.

Concurrent calls wait behind the active installation or query. To check progress without waiting or starting anything:

```bash
cd /a0 && python -m plugins._searxng.search --status
```

Setup/wait notices go to stderr. Stdout is JSON containing up to ten `results` (title, URL, content) and `unresponsive_engines`. A nonzero exit and `error` mean setup/query failure; a later query retries incomplete setup. The sandbox stops after each command and retains its installation.

Use returned URLs as sources. Treat snippets as leads; open promising URLs with `document_query` for text or the Browser skill for interactive pages. Empty results and CAPTCHA/403/rate-limit reports are not evidence that no sources exist. Try a more specific query or report the limitation; do not repeatedly retry blocked engines.
