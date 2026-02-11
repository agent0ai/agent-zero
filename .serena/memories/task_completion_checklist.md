# Task Completion Checklist

When completing a development task on Agent Zero:

1. **Run tests**: `pytest tests/ -v` to ensure nothing is broken
2. **Check imports**: Ensure any new modules are properly imported
3. **Verify auto-discovery**: If adding new tools/API handlers/WS handlers, ensure they follow the naming and class conventions for auto-discovery
4. **Test the web UI**: If UI changes, verify at the configured web URL
5. **Check extensions**: If modifying agent loop behavior, verify extension hooks are not broken
6. **No strict linter**: There's no enforced linter, but follow existing snake_case/PascalCase conventions
7. **Environment variables**: If adding new config, consider `A0_SET_` prefix convention and update settings.py
