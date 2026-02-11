# Code Style and Conventions

## Python
- **Python version**: 3.x (modern syntax: type hints with `|` union, f-strings)
- **Type hints**: Used but not mandatory everywhere; `str | None` style preferred over `Optional[str]`
- **Naming**: snake_case for functions/variables, PascalCase for classes
- **Imports**: Standard lib first, then third-party, then local modules
- **Dataclasses**: Used for configuration objects (e.g., `AgentConfig`, `ModelConfig`)
- **Async**: Heavy use of `asyncio` and `nest_asyncio`; many API handlers are async
- **No strict linting enforced**: No flake8/black/ruff config found in project root
- **Docstrings**: Minimal; code is expected to be self-documenting

## JavaScript (WebUI)
- Vanilla JS (no React/Vue/Angular)
- HTML templates with placeholder replacement
- Standard browser APIs

## Project Conventions
- Tools are Python classes in `python/tools/`, auto-discovered
- API handlers are classes extending `ApiHandler` in `python/api/`, auto-discovered
- WebSocket handlers in `python/websocket_handlers/`, namespace-based discovery
- Extensions are organized by lifecycle event in `python/extensions/` subdirectories
- Prompts are Markdown files in `prompts/`, some with `.py` extension for dynamic content
- Files ending with `._py` (e.g., `browser_do._py`) appear to be disabled/archived tools
- Settings are managed via a JSON-based settings system (`python/helpers/settings.py`)
