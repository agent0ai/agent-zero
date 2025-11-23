# Agent Zero Codebase Structure

## Root Level Files
- `agent.py` - Core agent implementation (main Agent class)
- `models.py` - Model providers and configurations
- `initialize.py` - Framework initialization logic
- `preload.py` - Pre-initialization routines
- `prepare.py` - Environment preparation
- `run_ui.py` - Web UI launcher
- `run_cli.py` - CLI launcher
- `run_tunnel.py` - Tunnel manager for remote access

## Core Python Package Structure

### `/python/api/`
API endpoints for web interface:
- Message handling
- Settings management
- File operations
- Project management

### `/python/helpers/`
Utility modules (60+ files):
- **Core Systems**: 
  - `call_llm.py` - LLM interaction
  - `memory.py` - Memory management
  - `vector_db.py` - Knowledge base
  - `tool.py` - Tool base class
  
- **Integration**:
  - `docker.py` - Container management
  - `mcp_handler.py` - MCP protocol
  - `browser_use.py` - Browser automation
  - `shell_local.py` / `shell_ssh.py` - Command execution
  
- **Features**:
  - `projects.py` - Project isolation
  - `task_scheduler.py` - Scheduled tasks
  - `knowledge_import.py` - Document ingestion
  - `persist_chat.py` - Session persistence

### `/python/tools/`
Built-in agent tools (20+ tools):
- **Core Tools**:
  - `code_execution_tool.py` - Execute code/terminal commands
  - `call_subordinate.py` - Multi-agent delegation
  - `response.py` - User communication
  
- **Memory Tools**:
  - `memory_save.py` - Store information
  - `memory_load.py` - Retrieve information
  - `memory_delete.py` - Remove entries
  - `memory_forget.py` - Bulk cleanup
  
- **Specialized**:
  - `browser_agent.py` - Web browsing
  - `search_engine.py` - Web search
  - `document_query.py` - Document analysis
  - `scheduler.py` - Task scheduling

### `/python/extensions/`
Modular extensions for additional functionality

## Configuration & Data

### `/prompts/`
System prompts and templates:
- Agent behavior definitions
- Tool usage instructions
- Response formatting
- Custom project prompts

### `/instruments/`
Runtime scripts and utilities:
- Custom executable tools
- Helper scripts
- Project-specific instruments

### `/knowledge/`
FAISS vector database storage:
- Document embeddings
- Indexed content
- Project-isolated knowledge

### `/memory/`
Persistent memory storage:
- Agent memories
- Conversation context
- Learned patterns
- Project-specific memory

## Web Interface

### `/webui/`
- `/css/` - Stylesheets
- `/js/` - JavaScript modules
- `/public/` - Static assets
- HTML templates
- Real-time communication

## Development & Testing

### `/tests/`
Unit and integration tests:
- `rate_limiter_test.py`
- `chunk_parser_test.py`
- `email_parser_test.py`
- `test_fasta2a_client.py`
- `test_file_tree_visualize.py`

### `/.vscode/`
VS Code configuration:
- `launch.json` - Debug profiles
- `extensions.json` - Recommended extensions
- `settings.json` - Project settings

### `/docs/`
Documentation:
- `architecture.md` - System design
- `development.md` - Dev guide
- `installation.md` - Setup instructions
- `usage.md` - User guide
- `extensibility.md` - Extension guide

## Docker Support

### `/docker/`
Container configuration:
- Dockerfile definitions
- Docker Compose setup
- Runtime environment

## Temporary & Generated

### `/logs/`
HTML-formatted chat logs

### `/tmp/`
Temporary runtime data

### `/usr/`
User-specific data

## Key Architectural Patterns

1. **Tool Discovery**: Tools automatically discovered from `/python/tools/`
2. **Prompt Templates**: Behavior defined in markdown prompts
3. **Project Isolation**: Each project has separate memory/knowledge/prompts
4. **Hierarchical Agents**: Superior-subordinate agent relationships
5. **Memory Types**: Short-term (context) and long-term (persistent)
6. **Extension System**: Modular additions without core changes
7. **Model Agnostic**: Support for multiple LLM providers

## File Naming Conventions
- Python files: `snake_case.py`
- Disabled tools: `tool_name._py`
- Test files: `*_test.py` or `test_*.py`
- Prompts: `descriptive.name.md`
- Memories: Structured keys with areas