# Hot-Reload System

## Overview

The Hot-Reload System enables **instant tool and extension reloading** without Docker restarts, reducing development iteration time from 30-60 seconds to **less than 1 second**.

## Features

- **Automatic File Monitoring**: Watches `python/tools/`, `python/extensions/`, and `prompts/` directories
- **Safe Module Reloading**: Uses `importlib.reload()` with error handling and rollback
- **Dependency Tracking**: Analyzes module dependencies using AST parsing
- **Cache Management**: Intelligent module caching with versioning
- **WebSocket Updates**: Real-time UI notifications (future feature)
- **DevTools Panel**: Web UI panel showing reload status and statistics

## Architecture

### Components

1. **hot_reload.py** - File monitoring using watchdog library
   - `FileWatcher`: Manages file system observers
   - `HotReloadManager`: Singleton coordinator
   - Debouncing to prevent duplicate events

2. **module_cache.py** - Module caching and safe reloading
   - `ModuleCache`: Caches loaded modules with metadata
   - `DependencyAnalyzer`: AST-based import analysis
   - Rollback mechanism on reload failures

3. **hot_reload_integration.py** - Integration with Agent Zero
   - Connects file changes to tool/extension reloading
   - Invalidates Agent Zero's internal caches
   - Tracks reload statistics

4. **hot_reload_status.py** - API endpoint
   - Provides status and statistics
   - Accessible via `/hot_reload_status`

5. **hot_reload_panel.js** - Web UI component
   - Real-time status indicator
   - Reload statistics display
   - Auto-updates every 5 seconds

## Installation

### Prerequisites

Install the watchdog library:

```bash
pip install watchdog
```

Or add to `requirements.txt`:

```
watchdog>=3.0.0
```

### Configuration

Enable/disable hot-reload in `.env`:

```bash
# Enable hot-reload (default: true)
HOT_RELOAD_ENABLED=true
```

## Usage

### Starting Agent Zero

The hot-reload system starts automatically when you run:

```bash
python run_ui.py
```

You'll see:

```
Hot-reload manager initialized
Hot-reload file watcher started
Hot-reload system initialized
```

### Developing Tools

1. Edit a tool file:

```bash
vim D:\projects\agent-zero\python\tools\code_execution_tool.py
```

2. Save the file

3. Hot-reload detects the change and reloads automatically:

```
Hot-Reload: MODIFIED - code_execution_tool.py
Reloading module: tools.code_execution_tool
Successfully reloaded: tools.code_execution_tool
Tools cache invalidated
```

4. The tool is now available with your changes - **no restart needed**

### Developing Extensions

Same workflow applies to extensions:

```bash
vim D:\projects\agent-zero\python\extensions\message_loop_end\_10_organize_history.py
# Make changes, save
# Hot-reload handles the rest
```

### DevTools Panel

Open Agent Zero's web UI to see the hot-reload panel (bottom-right corner):

- **Status Indicator**: Green dot = active, Red dot = inactive
- **Statistics**:
  - Reloads: Total reload attempts
  - Success: Successful reloads
  - Failures: Failed reloads
  - Cached Modules: Currently cached modules

### API Access

Query hot-reload status programmatically:

```bash
# Get status
curl -X POST http://localhost:50001/hot_reload_status \
  -H "Content-Type: application/json" \
  -d '{"action": "status"}'

# Get statistics
curl -X POST http://localhost:50001/hot_reload_status \
  -H "Content-Type: application/json" \
  -d '{"action": "stats"}'
```

## How It Works

### File Change Detection

1. Watchdog monitors configured directories
2. File system events trigger callbacks (created, modified, deleted)
3. Events are debounced to prevent duplicates (500ms window)

### Module Reloading

1. File change event received
2. Module type determined (tool, extension, prompt)
3. Module loaded with `importlib.util.spec_from_file_location()`
4. Previous version backed up
5. New version executed
6. On success: cache updated, old caches invalidated
7. On failure: rollback to previous version

### Cache Invalidation

When a module reloads:

- **Tools**: `extract_tools._cache` cleared
- **Extensions**: `extension._cache` cleared
- **Module Cache**: Specific module entry updated

This forces Agent Zero to rediscover and use the new versions.

## Error Handling

### Syntax Errors

If you save a file with syntax errors:

```python
# Broken code
def my_tool(
    # Missing closing parenthesis
```

Hot-reload will:

1. Attempt to load the module
2. Catch the `SyntaxError`
3. Display error message
4. **Rollback to the last working version**
5. Increment failure counter

### Import Errors

If your code has import errors:

```python
import non_existent_module
```

Same behavior as syntax errors - rollback to last working version.

### Runtime Errors

Errors during module initialization are caught and logged.

## Performance

- **File Change Detection**: < 10ms
- **Module Reload**: 50-200ms
- **Cache Invalidation**: < 10ms
- **Total**: **< 500ms** vs 30-60 seconds for Docker restart

## Limitations

1. **Class Instance State**: Existing instances won't be updated
   - Only new instances use the reloaded code
   - Agent Zero creates fresh tool instances per execution

2. **Global State**: Module-level variables reset on reload
   - Use agent.set_data() for persistent state

3. **Circular Dependencies**: May cause reload issues
   - Keep tool/extension dependencies simple

4. **System Modules**: Cannot reload Python stdlib modules

## Troubleshooting

### Hot-Reload Not Starting

Check logs for:

```
Hot-reload disabled
```

Solution: Set `HOT_RELOAD_ENABLED=true` in `.env`

### Changes Not Detected

1. Verify file is in monitored directory:
   - `python/tools/`
   - `python/extensions/`
   - `prompts/`

2. Check file extension:
   - `.py` for Python files
   - `.md` or `.txt` for prompts

3. Ensure watchdog is installed:

```bash
pip install watchdog
```

### Reload Failures

Check the DevTools panel for failure count.

View detailed errors in terminal output.

If persistent issues, restart Agent Zero:

```bash
# Stop
Ctrl+C

# Start
python run_ui.py
```

## Advanced Usage

### Custom Watch Directories

Edit `hot_reload.py` to add directories:

```python
def initialize(self, enabled: bool = True) -> None:
    # Add custom directory
    self.watcher.add_watch(WatchConfig(
        path="my_custom_tools",
        patterns=["*.py"],
        recursive=True
    ))
```

### Reload Callbacks

Register custom callbacks for reload events:

```python
from python.helpers.hot_reload_integration import get_hot_reload_integration

def my_callback(event):
    print(f"File changed: {event.path}")

integration = get_hot_reload_integration()
integration.reload_manager.add_reload_callback(my_callback)
```

### Dependency Analysis

Analyze module dependencies:

```python
from python.helpers.module_cache import get_module_cache

cache = get_module_cache()
cache.analyze_dependencies()

# Get reload order
order = cache.get_reload_order("tools.code_execution_tool")
print(f"Reload order: {order}")
```

## Future Enhancements

- [ ] WebSocket real-time notifications
- [ ] UI button to manually trigger reloads
- [ ] Dependency graph visualization
- [ ] Hot-reload for Python helper modules
- [ ] Automatic test execution on reload
- [ ] Performance profiling per reload

## Implementation Notes

### Modular Design

Following DRY principles:

- `hot_reload.py`: File watching (single responsibility)
- `module_cache.py`: Module management (single responsibility)
- `hot_reload_integration.py`: Agent Zero integration (single responsibility)

No "god classes" - each module has a clear, focused purpose.

### Thread Safety

- File watching runs in separate threads (watchdog)
- Module reloading is synchronous to prevent race conditions
- Cache operations are not currently thread-safe (single-threaded reload)

## Credits

- **Watchdog Library**: File system monitoring
- **importlib**: Python's dynamic import system
- **AST Module**: Dependency analysis
