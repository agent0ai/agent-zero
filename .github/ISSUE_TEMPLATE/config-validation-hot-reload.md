---
    title: "🔧 Config: Schema validation & hot-reload support"
    labels: "enhancement, configuration, devops"
    ---

    ## Problem Statement

    Agent Zero's configuration system lacks:

    1. **No validation** - Invalid configs cause runtime errors
    2. **No hot-reload** - Restart required for config changes
    3. **No schema** - Users guess valid options
    4. **Partial persistence** - Settings UI saves to `usr/settings.json` but not validated

    ## Current Issues

    ### Example 1: Invalid model name
    ```yaml
    chat_model:
      provider: "openai"
      name: "gpt-99"  # ❌ Invalid, but only fails at runtime
    ```

    ### Example 2: Missing required fields
    ```yaml
    # settings.json with missing 'workdir_path'
    {
      "theme": "dark"
      # Missing required fields → default applied silently? Or crash?
    }
    ```

    ### Example 3: No live updates
    - Admin changes API key in Settings UI
    - Must restart container to take effect
    - Disrupts active agent conversations

    ## Proposed Solution

    ### 1. JSON Schema for Configuration

    Create `conf/settings-schema.json`:

    ```json
    {
      "$schema": "http://json-schema.org/draft-07/schema#",
      "type": "object",
      "properties": {
        "workdir_path": {
          "type": "string",
          "description": "Working directory for file operations",
          "default": "/usr/workdir"
        },
        "chat_model": {
          "type": "object",
          "properties": {
            "provider": {
              "type": "string",
              "enum": ["openai", "anthropic", "openrouter", "gemini", "huggingface"]
            },
            "name": {
              "type": "string",
              "description": "Model name as recognized by provider"
            },
            "temperature": {
              "type": "number",
              "minimum": 0,
              "maximum": 2,
              "default": 0.7
            },
            "max_tokens": {
              "type": "integer",
              "minimum": 1,
              "maximum": 100000
            }
          },
          "required": ["provider", "name"]
        },
        "mcp_servers": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "name": {"type": "string"},
              "type": {"type": "string", "enum": ["stdio", "sse", "streamable-http"]},
              "url": {"type": "string", "format": "uri"},
              "command": {"type": "string"}
            },
            "required": ["name"]
          }
        }
      }
    }
    ```

    ### 2. Config Validation on Load

    ```python
    import jsonschema

    def validate_settings(settings: dict) -> dict:
        schema = json.load(open('conf/settings-schema.json'))
        try:
            jsonschema.validate(settings, schema)
            return settings
        except jsonschema.ValidationError as e:
            raise ConfigValidationError(f"Invalid settings: {e.message}")
    ```

    Call this on:
    - Startup (load from `usr/settings.json`)
    - Settings UI save
    - Environment variable application (`.env` → settings)

    ### 3. Hot-Reload Mechanism

    #### Option A: File Watcher (Simple)
    ```python
    import watchdog.observers
    import asyncio

    async def watch_settings_file():
        observer = watchdog.observers.Observer()
        observer.schedule(SettingsHandler(), path='/usr/settings.json')
        observer.start()
        while True:
            await asyncio.sleep(1)
            if settings_changed:
                reload_settings()
                broadcast_to_agents('settings_updated', new_settings)
    ```

    #### Option B: WebSocket Event (Better)
    ```python
    # Add to run_ui.py
    @app.post("/api/settings/reload")
    async def reload_settings_endpoint():
        await settings.reload()
        await AgentContext.log_to_all(type='info', content='Settings reloaded')
        return {"status": "reloaded"}
    ```

    User clicks "Reload Settings" in UI, or auto-reload after save.

    #### Option C: Signal-Based (Docker-friendly)
    ```python
    # In run_ui.py
    signal.signal(signal.SIGHUP, handle_sighup)

    def handle_sighup(signum, frame):
        settings.reload()
        print("Settings reloaded via SIGHUP")
    ```

    Docker-compose:
    ```bash
    docker kill -s HUP agent-zero
    ```

    ### 4. Settings UI Improvements

    1. **Real-time Validation**
       - Validate before save
       - Show errors inline
       - Preview effective configuration after merge

    2. **Safe Editing**
       - Show current value vs default value
       - Reset to default button per field
       - Diff view before commit

    3. **Import/Export**
       - Export current config as JSON
       - Import config with validation
       - Migration wizard from old → new schema

    ## Implementation Tasks

    1. **Create JSON Schema**
       - Document all settings with types, defaults, descriptions
       - Include nested schemas for `chat_model`, `mcp_servers`, etc.
       - Place in `conf/settings-schema.json`

    2. **Add Validation Layer**
       - Modify `python/helpers/settings.py`
       - Add `validate()` method
       - Call on load and save
       - Provide helpful error messages (which field, what's wrong)

    3. **Hot-Reload Implementation**
       - Choose approach (WebSocket endpoint recommended)
       - Add `/api/settings/reload` POST endpoint
       - Add "Reload" button in Settings UI
       - Handle agent context updates gracefully

    4. **Update Settings UI**
       - Add validation feedback (red borders, error text)
       - Show loading state during save
       - Auto-reload on successful save (optional)
       - Display effective config (merged from defaults, file, env)

    5. **Environment Variable Overrides**
       - Support `A0_SET_*` env vars (already exists)
       - Validate these too
       - Document precedence: env > file > defaults

    ## Testing

    - [ ] Valid configs pass validation
    - [ ] Invalid configs produce clear error messages
    - [ ] Hot-reload works without dropping connections
    - [ ] Agent contexts pick up new config within 5 seconds
    - [ ] Settings UI shows validation errors before save
    - [ ] Import/export round-trip preserves data
    - [ ] Backwards compatibility: old configs migrate to new schema

    ## Benefits

    - **Reliability:** Catch config errors before they crash
    - **UX:** No restarts needed for config changes
    - **Safety:** Clear error messages guide users
    - **Documentation:** Schema serves as living doc
    - **Automation:** Env vars validated too

    ## Risks

    - **Breaking changes:** New schema may reject old configs → provide migration tool
    - **Performance:** Validation on every save is cheap (<1ms), negligible
    - **Complexity:** Schema maintenance overhead

    ---
    *Proper configuration management is key to reliable operations.*
    