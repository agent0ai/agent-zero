# Agent Jumbo - Copilot Instructions

## Architecture Overview

Agent Jumbo is a **prompt-driven, hierarchical agentic framework** designed as an active personal AI assistant application. Almost nothing is hardcoded—behavior is controlled through prompts in `/prompts/` and code is dynamically loaded.

**Key architectural concepts:**

- **Agent hierarchy**: User → Agent 0 → subordinate agents (each can spawn subordinates)
- **AgentContext** ([agent.py](agent.py)) manages agent state, lifecycle, and communication
- **AgentConfig** defines model connections (chat, utility, embeddings, browser) and runtime settings
- **Tool execution** uses JSON responses from LLMs parsed via `DirtyJson` helper

## Directory Structure

| Path | Purpose |
|------|---------|
| `/prompts/` | All system prompts - **edit these to change agent behavior** |
| `/python/tools/` | Tool implementations (inherit from `Tool` base class) |
| `/python/extensions/` | Lifecycle hooks (e.g., `agent_init/`, `before_main_llm_call/`) |
| `/python/helpers/` | Utility functions (memory, files, tokens, etc.) |
| `/agents/{profile}/` | Agent profiles with custom prompts, tools, extensions |
| `/instruments/custom/` | Custom instruments - see [Instruments Index](#instruments-index) |
| `/knowledge/` | Knowledge base storage (RAG-indexed) |
| `/memory/` | Persistent agent memory (vector DB) |

---

## Testing

### Test Framework

- **pytest** with config in `pytest.ini` (testpaths=`tests/`, pythonpath=`.`)
- Tests use `tmp_path` fixtures for isolation

### Running Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/test_workflow_manager.py

# With coverage
pytest --cov=python --cov-report=html

# Verbose output
pytest -v tests/test_workflow_e2e.py
```

### Test Categories

| Pattern | Purpose |
|---------|---------|
| `test_*_manager.py` | Unit tests for business logic |
| `test_*_e2e.py` | End-to-end integration tests |
| `test_*_api.py` | API endpoint tests |
| `test_*_schema.py` | JSON schema validation |

### Writing Tests

```python
# tests/test_my_feature.py
import pytest
from instruments.custom.my_instrument.manager import MyManager

class TestMyFeature:
    @pytest.fixture(autouse=True)
    def setup_method(self, tmp_path):
        self.db_path = str(tmp_path / "test.db")
        self.manager = MyManager(self.db_path)

    def test_basic_operation(self):
        result = self.manager.create_item(name="Test")
        assert 'item_id' in result
        assert result['status'] == "created"
```

### Test Fixtures

Shared fixtures in `tests/fixtures/`:

- `workflow_sample_data.py` - Sample data generator for workflow engine
- `common.py` - Shared fixtures (paths, mocks, sample data)

Use fixtures for:

- Database path isolation (`tmp_path`)
- Sample data generation
- Mock agent contexts for tool testing

### Test Template

Copy `tests/_test_template.py` when creating new instrument tests.

---

## Docker & Container Development

### Runtime Architecture

Agent Jumbo runs in Docker for code execution isolation. The framework on your machine connects to a containerized runtime via SSH.

### Docker Commands

```bash
# Pull and run production image
docker pull agent0ai/agent-zero
docker run -p 50001:80 agent0ai/agent-zero

# Build local development image
docker build -f DockerfileLocal -t agent-jumbo-local .

# Run with local code mounted
docker run -p 50001:80 -v $(pwd):/a0 agent-jumbo-local
```

### Development with DevPod

```bash
# Initialize DevPod workspace
devpod up . --ide vscode

# Or with specific provider
devpod up . --provider docker --ide vscode
```

### SSH Code Execution Config

Configure in Settings UI or `.env`:

```env
CODE_EXEC_SSH_ENABLED=true
CODE_EXEC_SSH_ADDR=localhost
CODE_EXEC_SSH_PORT=55022
CODE_EXEC_SSH_USER=root
```

### Container Ports

| Port | Service |
|------|---------|
| 80 | Web UI |
| 22 | SSH (code execution) |
| 9000-9009 | Additional services |

---

## Instruments Index

Instruments are callable Python procedures that extend agent capabilities. Located in `/instruments/custom/`.

### Available Instruments

| Instrument | Purpose | Key Files |
|------------|---------|-----------|
| `workflow_engine` | Multi-stage workflow orchestration | `workflow_manager.py`, `workflow_db.py` |
| `business_xray` | Business health analysis & visualization | `comprehensive_xray.py` |
| `virtual_team` | Multi-agent team coordination | - |
| `customer_lifecycle` | Customer journey management | - |
| `diagram_architect` | Architecture diagram generation | - |
| `sales_generator` | Sales content automation | - |
| `portfolio_manager` | Asset/project portfolio tracking | - |
| `property_manager` | Real estate management | - |
| `skill_importer` | Skill/capability ingestion | - |
| `plugin_marketplace` | Plugin discovery & installation | - |
| `ralph_loop` | Iterative refinement loops | - |
| `deployment_orchestrator` | Deployment pipeline management | - |
| `project_scaffold` | Project templating | - |
| `security_monitor` | Security scanning | - |
| `claude_sdk` | Claude Code SDK integration | - |
| `ai_migration` | AI-assisted code migration | - |

### Creating Instruments

**Required Structure:**

```
instruments/custom/my_instrument/
├── __init__.py           # Package marker
├── my_instrument.md      # Agent-facing documentation
├── main.py               # Entry point (or manager.py)
├── schemas/              # JSON schemas for validation
│   └── config.schema.json
├── templates/            # Output templates
└── data/                 # Persistent data (if needed)
```

**Best Practices:**

1. **Separation of concerns**: Split into `*_manager.py` (logic), `*_db.py` (persistence), `*_visualizer.py` (output)
2. **Schema validation**: Use jsonschema for input validation
3. **Typed returns**: Return structured dicts with `status`, `error`, or domain-specific keys
4. **Database isolation**: Use SQLite with path passed to constructor for testability
5. **Markdown docs**: Create `{instrument_name}.md` describing capabilities for the agent

**Example Manager Pattern:**

```python
# instruments/custom/my_instrument/manager.py
import json
import jsonschema
from pathlib import Path
from .db import MyDatabase

class MyInstrumentManager:
    def __init__(self, db_path: str):
        self.db = MyDatabase(db_path)
        self._schema_cache = {}
        self._load_schemas()

    def _load_schemas(self):
        schema_dir = Path(__file__).parent / "schemas"
        for schema_file in schema_dir.glob("*.schema.json"):
            with open(schema_file) as f:
                name = schema_file.stem.replace(".schema", "")
                self._schema_cache[name] = json.load(f)

    def create_item(self, name: str, **kwargs) -> dict:
        # Validate, persist, return structured result
        item_id = self.db.save_item(name=name, **kwargs)
        return {"item_id": item_id, "status": "created"}
```

---

## MCP Integration

Agent Jumbo supports [Model Context Protocol](https://modelcontextprotocol.io/) for external integrations.

### Configuration

MCP servers configured in Settings UI or `mcp_config_claude.json`:

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/projects"]
    },
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"]
    }
  }
}
```

### Available MCP Servers

| Server | Purpose |
|--------|---------|
| `filesystem` | File read/write/search |
| `github` | Repo, issue, PR management |
| `brave-search` | Web search |
| `fetch` | Web page content extraction |
| `memory` | Persistent knowledge graph |
| `sqlite` / `postgres` | Database operations |
| `puppeteer` | Browser automation |
| `sequential-thinking` | Extended reasoning |

### External API

Agent Jumbo exposes APIs for external integration:

- `POST /api_message` - Send messages, receive responses
- `GET/POST /api_log_get` - Retrieve conversation logs
- Use `X-API-KEY` header (generated from credentials in Settings)

### Creating Custom MCP Servers

For project-specific integrations, create MCP servers:

1. **Using Python (fastmcp)**:

```python
# mcp_servers/my_server.py
from fastmcp import FastMCP

mcp = FastMCP("my-server")

@mcp.tool()
def my_tool(query: str) -> str:
    """Tool description for the agent."""
    return f"Result for: {query}"

if __name__ == "__main__":
    mcp.run()
```

2. **Register in `mcp_config_claude.json`**:

```json
{
  "mcpServers": {
    "my-server": {
      "command": "python",
      "args": ["mcp_servers/my_server.py"],
      "description": "Custom integration server"
    }
  }
}
```

3. **Available in Settings UI** for runtime configuration

---

## WebUI Architecture

The frontend uses **Alpine.js** with a store-based state management pattern.

### Directory Structure

```
webui/
├── index.js              # Main app, message handling
├── js/api.js             # API client with CSRF handling
├── components/
│   ├── chat/             # Chat UI components
│   ├── settings/         # Settings panels (mcp/, memory/, security-cockpit/)
│   ├── sidebar/          # Navigation and chat list
│   ├── notifications/    # Notification system
│   └── modals/           # Dialog components
```

### Store Pattern

Each feature has a store file (`*-store.js`) managing state:

```javascript
// components/feature/feature-store.js
import Alpine from "alpinejs";

export const store = {
  items: [],
  loading: false,

  async fetchItems() {
    this.loading = true;
    const data = await callJsonApi("/api/items", {});
    this.items = data.items;
    this.loading = false;
  }
};

Alpine.store("feature", store);
```

### API Conventions

- All API calls go through `fetchApi()` which handles CSRF tokens
- Use `callJsonApi(endpoint, data)` for JSON POST requests
- Endpoints are in `/python/api/` (one file per endpoint)

---

## Prompt Engineering

### JSON Response Format

Agent responses must be valid JSON with these fields:

```json
{
  "thoughts": ["Step-by-step reasoning..."],
  "headline": "Brief action description for UI",
  "tool_name": "tool_to_use",
  "tool_args": { "arg1": "value1" }
}
```

### Writing Tool Prompts

Tool prompts in `prompts/agent.system.tool.*.md` should:

1. Start with `### tool_name:` header
2. Describe purpose in terse, instruction-style prose
3. List all args with types and requirements
4. Include JSON usage examples with `~~~json` blocks

### Prompt Tips

- Use terse, instruction-style language (no articles, minimal words)
- Include concrete examples from the codebase
- Define edge cases and error handling
- Specify when `break_loop: true` vs `false`

---

## Memory System

### Architecture

- **Storage**: FAISS vector database per memory subdirectory
- **Embeddings**: Cached via `CacheBackedEmbeddings`
- **Areas**: `main` (facts), `solutions` (code/fixes), `fragments`, `instruments`

### Memory Flow

```
User message → Automatic recall (if enabled) → Agent processes
     ↓
Agent saves → memory_save tool → FAISS index
     ↓
Future queries → Similarity search → Relevant memories injected
```

### Configuration

```python
# Key settings in Settings UI or .env
MEMORY_RECALL_ENABLED=true          # Enable automatic recall
MEMORY_RECALL_SIMILARITY_THRESHOLD=0.7  # Match threshold (0-1)
MEMORY_MEMORIZE_ENABLED=true        # Allow agent to save
MEMORY_MEMORIZE_CONSOLIDATION=true  # Merge similar memories
```

### Subdirectories

- Each agent profile can have isolated memory: `memory/{subdir}/`
- Knowledge base: `knowledge/{subdir}/` (RAG-indexed)
- Secure partitions: `secure_*` prefixes require auth

---

## Creating Tools

1. Create `python/tools/{tool_name}.py` inheriting from `Tool`:

```python
from python.helpers.tool import Tool, Response

class MyTool(Tool):
    async def execute(self, **kwargs) -> Response:
        result = self.args.get("param_name")
        return Response(message="result", break_loop=False)
```

2. Create matching prompt at `prompts/agent.system.tool.{tool_name}.md` with JSON usage examples
3. Register in `prompts/agent.system.tools.md` using `{{ include "agent.system.tool.{tool_name}.md" }}`

---

## Creating Extensions

Extensions hook into agent lifecycle. Place in `/python/extensions/{hook_name}/`:

```python
from python.helpers.extension import Extension

class MyExtension(Extension):
    async def execute(self, **kwargs):
        self.agent  # Access agent instance
```

**Extension points**: `agent_init`, `before_main_llm_call`, `message_loop_start`, `monologue_start`, `response_stream`, `system_prompt`, `tool_execute_before`, `tool_execute_after`

---

## Agent Profiles

Override defaults per-profile in `/agents/{profile}/`:

- `prompts/` - Override default prompts
- `tools/` - Override/add tools (same filename replaces default)
- `extensions/` - Override/add extensions

---

## Development Commands

```bash
# Setup
pip install -r requirements.txt
pip install -r requirements.dev.txt
playwright install chromium

# Run UI
python run_ui.py              # Port 5000
python run_ui.py --port=5555  # Custom port

# Testing
pytest                        # All tests
pytest -v tests/test_*.py     # Verbose

# Linting
ruff check .                  # Lint
ruff format .                 # Format

# Local CI (requires act)
./scripts/run-ci-local.sh           # All jobs
./scripts/run-ci-local.sh lint      # Lint only
./scripts/run-ci-local.sh test      # Tests only
./scripts/run-ci-local.sh --list    # List jobs

# Docker
docker build -f DockerfileLocal -t agent-jumbo-local .

# Pre-commit hooks
pre-commit install
pre-commit run --all-files
```

---

## Key Patterns

- **Model abstraction**: All LLM calls via [models.py](models.py) using LiteLLM
- **Memory**: FAISS vector DB in `/python/helpers/memory.py`
- **Settings**: Runtime config in `/python/helpers/settings.py`, user `.env` file
- **Dirty JSON**: Fault-tolerant response parsing via `DirtyJson` helper
- **Async-first**: Most tool/extension methods are `async`

---

## Troubleshooting

### Common Issues

| Problem | Solution |
|---------|----------|
| SSH connection refused | Check Docker is running, verify `CODE_EXEC_SSH_PORT` matches container |
| Tool not found | Ensure prompt registered in `agent.system.tools.md` |
| Memory not recalling | Check `MEMORY_RECALL_ENABLED=true` in settings |
| DirtyJson parse errors | Agent response may have unclosed braces; check LLM output |
| Extension not loading | Verify filename matches pattern `_XX_name.py` for ordering |

### Debugging Tips

```bash
# Check Docker container status
docker ps -a | grep agent-jumbo

# View container logs
docker logs <container_id>

# Test SSH connection manually
ssh -p 55022 root@localhost

# Run with verbose logging
LITELLM_LOG=DEBUG python run_ui.py
```

### Tool Execution Flow

1. Agent outputs JSON with `tool_name` and `tool_args`
2. `DirtyJson` parses (tolerant of minor errors)
3. Tool class loaded from `/python/tools/` or `/agents/{profile}/tools/`
4. `before_execution()` → `execute()` → `after_execution()`
5. Response returned to agent context

### Memory System

- **Save**: `memory_save` tool → FAISS vector DB
- **Recall**: Triggered by `memory_load` or automatic recall (if enabled)
- **Areas**: `main`, `solutions`, `fragments`
- **Similarity threshold**: Default 0.7, adjust in settings

---

## When Modifying This Codebase

| Goal | Action |
|------|--------|
| Change agent behavior | Edit prompts in `/prompts/` |
| Add capabilities | Create tool + prompt in `/python/tools/` |
| Intercept lifecycle | Use extensions in `/python/extensions/` |
| Per-agent customization | Use profiles in `/agents/{profile}/` |
| Add complex features | Create instrument in `/instruments/custom/` |
| Test features | Add pytest tests in `/tests/` |
