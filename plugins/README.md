# Agent Zero Plugins

This directory contains default plugins shipped with Agent Zero.

## Plugin Architecture

Agent Zero uses a unified capability-based plugin system where a single `plugin.json` manifest declares all capabilities via a `provides` dictionary. Each capability type maps to an integration point in the framework.

## Plugin Structure

Each plugin directory should contain:
- `plugin.json` - Manifest file with capability declarations
- Capability-specific files organized by type (helpers, tools, extensions, api, ui, etc.)
- Other assets (CSS, images, documentation)

## Manifest Schema

The `plugin.json` uses a `provides` dict where keys are integration point types:

```json
{
  "id": "my-plugin",
  "name": "My Plugin",
  "version": "1.0.0",
  "author": "Author Name",
  "description": "Plugin description",
  "tags": ["tag1", "tag2"],
  "provides": {
    "helper": [
      { "module": "helpers/my_helper.py", "description": "Helper module description" }
    ],
    "tool": [
      { "module": "tools/my_tool.py", "description": "Tool description" }
    ],
    "extension": [
      { "module": "extensions/hook_name/my_extension.py", "description": "Extension description" }
    ],
    "api": [
      { "module": "api/my_api.py", "description": "API endpoint description" }
    ],
    "ui": {
      "component": "ui/component.html",
      "module": "ui/main.js",
      "description": "UI component description"
    }
  }
}
```

## Capability Types

- **helper**: Python modules providing reusable functionality (imported via proxy or direct)
- **tool**: Agent tools extending agent capabilities
- **extension**: Extension hooks that run at specific lifecycle points
- **api**: Flask API endpoints (ApiHandler subclasses)
- **ui**: Frontend components loaded via `<x-extension>` tags
- **prompt**: Custom prompt templates
- **knowledge**: Knowledge base files and directories
- **instrument**: Custom instrumentation and monitoring

## Using Plugins

### UI Components
```html
<x-extension id="plugin-id"></x-extension>
```

### Backend Capabilities
Backend capabilities (helpers, tools, extensions, APIs) are automatically discovered and integrated when the plugin is loaded.

## User Plugins

User-created plugins should be placed in one of the following directories:

- `/usr/plugins/` (Global user plugins)
- `/usr/projects/<project_name>/.a0proj/plugins/` (Project-specific plugins)

Note: `/usr/` refers to the Agent Zero user data directory in the application root, not the system `/usr` directory.

User plugins with the same ID as repo plugins will completely override the repo version.

## Documentation

See [docs/extensibility.md](../docs/extensibility.md) for complete documentation on creating plugins.
