# Unified Plugin System - Implementation Summary

This document provides a technical overview of the Plugin System implementation in Agent Zero.

## Overview

The Plugin System allows users and the community to create full-stack plugins that integrate seamlessly with Agent Zero. It supports backend capabilities (API endpoints, tools, helpers) and frontend UI extensions. It uses a manifest-driven approach (`plugin.json`) to declare capabilities.

## Architecture

### Components

1. Backend Plugin Discovery (`python/helpers/plugins.py`)
   - Resolves plugin directories across repo (`plugins/`) and user (`usr/plugins/`) locations.
   - Loads and validates `plugin.json` manifests.
   - Provides `import_plugin_module()` for dynamic dependency injection, replacing static imports.
   - Implements override logic (user plugins override repo plugins).

2. API Endpoints
   - `POST /plugins_resolve` - Resolves a plugin manifest by ID (for frontend).
   - `GET/POST /plugins_list` - Lists all available plugins.
   - `GET /plugins/<id>/<path>` - Serves plugin static assets (UI, scripts).

3. Frontend Plugin Loader (`webui/js/plugins.js`)
   - Discovers and loads `<x-extension>` tags.
   - Fetches plugin manifests via `/plugins_resolve`.
   - Path Traversal Strategy: Integrates with the standard component loader by adjusting paths (e.g., prepending `components/../` to plugin URLs) to bypass default path restrictions without modifying the core loader.
   - Handles module imports and props merging.

4. Standard Component Loader (`webui/js/components.js`)
   - Vanilla Implementation: Remains unmodified to ensure stability and compatibility.
   - Enforces `components/` prefix for all loaded resources.
   - Used by `plugins.js` via relative path traversal to load plugin UI components.

5. DOM Integration
   - Automatic loading on DOM ready.
   - MutationObserver for dynamic plugin injection.
   - Alpine.js integration via `globalThis.xAttrs()`.

## File Structure

```
/plugins/                    # Repo plugins (default)
  ├── memory/
  │   ├── plugin.json       # Manifest
  │   ├── api/              # Backend endpoints
  │   ├── tools/            # Agent tools
  │   ├── helpers/          # Python helpers
  │   ├── ui/               # Frontend components
  │   │   ├── memory-dashboard.html
  │   │   └── memory-dashboard-store.js
  │   └── prompts/          # System prompts
  └── README.md

/usr/plugins/               # User plugins (override)
  ├── my-plugin/
  │   ├── plugin.json
  │   └── ...
  └── README.md
```

## Plugin Manifest Schema

```json
{
  "id": "plugin-id",           // Required: Must match directory name
  "name": "Display Name",       // Optional: Human-readable name
  "provides": {
    "api": [
        { "module": "api/my_endpoint.py", "description": "..." }
    ],
    "tool": [
        { "module": "tools/my_tool.py", "description": "..." }
    ],
    "ui": {
        "component": "ui/index.html",
        "module": "ui/main.js"
    },
    "prompt": [
        { "module": "prompts/system.md", "description": "..." }
    ]
  },
  "props": {                    // Optional: Default UI properties
    "key": "value"
  }
}
```

## Usage

### Creating a Plugin

1. Create plugin directory: `plugins/my-plugin`
2. Create `plugin.json` declaring provided capabilities.
3. Implement backend modules in `api/`, `tools/`, etc.
4. Implement frontend components in `ui/`.

### Using Plugin Capabilities

Backend (Python):
Instead of static imports, use the dynamic loader:
```python
from python.helpers.plugins import import_plugin_module

# Dynamically load a helper from the 'memory' plugin
memory = import_plugin_module("memory", "helpers/memory.py")
memory.some_function()
```

Frontend (HTML/JS):
Plugins can be embedded via `<x-extension>` or loaded dynamically via `openModal`.
```javascript
// Open a plugin component in a modal
// Uses relative path to traverse out of 'components/' and into 'plugins/'
openModal("../plugins/my-plugin/ui/dashboard.html");
```
