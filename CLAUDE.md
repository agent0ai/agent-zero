# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Agent Zero is a dynamic, open-source agentic AI framework designed as a personal, organic assistant that grows and learns with use. It's not a pre-programmed solution but a general-purpose framework that uses the computer as a tool to accomplish goals through hierarchical multi-agent cooperation, persistent memory, and extensible tool systems. Everything is prompt-driven with zero hard-coded logic.

**Key Facts:**
- Latest version: v0.9.7 (Projects feature with isolated workspaces)
- Fully Dockerized with web UI and CLI interfaces
- Completely customizable and extensible (24+ extension points)
- Supports 20+ LLM providers via LiteLLM
- Self-evolving meta-learning system (learns from usage patterns)

## Common Development Commands

### Running the Application

```bash
# Start the Flask web UI server on port 50001
python run_ui.py

# Start the remote tunnel service for external access
python run_tunnel.py

# Run the agent directly from CLI
python agent.py

# Docker - Pull and run the pre-built image
docker pull agent0ai/agent-zero
docker run -p 50001:80 agent0ai/agent-zero
```

### Testing

```bash
# Run all tests
python -m pytest tests/

# Run a specific test file
python -m pytest tests/rate_limiter_test.py

# Run tests with verbose output
python -m pytest tests/ -v

# Run a specific test function
python -m pytest tests/rate_limiter_test.py::test_function_name
```

### Installation & Setup

```bash
# Install dependencies
pip install -r requirements.txt

# First-time setup/initialization
python initialize.py

# For development, install in editable mode
pip install -e .
```

## Architecture & Structure

### High-Level Architecture

Agent Zero uses a **hierarchical multi-agent system** with these core components:

1. **Message Loop** (the heartbeat) - Located in `agent.py:356` in the `monologue()` method
   - Continuous loop that processes agent reasoning
   - 24+ extension points for customization
   - Streams LLM responses in real-time
   - Executes tools and processes their results

2. **Tool System** - Dynamic capability execution
   - ~20 built-in tools (code execution, browser, memory, search, etc.)
   - Tools are discovered and loaded dynamically from `python/tools/`
   - Tools are extracted from LLM responses by `extract_tools.py`
   - User can create custom tools by adding classes to `python/tools/`

3. **Memory System** - Three-tier persistent learning
   - FAISS vector database for semantic search of embeddings
   - Memory areas: MAIN (facts), FRAGMENTS (snippets), SOLUTIONS (patterns), INSTRUMENTS (code)
   - Auto-extracted and manually added memories persist across sessions
   - Semantic search retrieves relevant memories when processing new messages

4. **Extension System** - 24 hook points for non-invasive customization
   - Located in `python/extensions/` with numbered files for execution order
   - Extension points throughout the message loop (start, end, before/after LLM calls, etc.)
   - Can modify state, history, prompts without changing core code

5. **Prompt System** - Hierarchical, fallback-based loading
   - Agent profile prompts: `agents/[profile]/prompts/`
   - Default prompts: `prompts/` (fallback)
   - Framework prompts: Built-in system instructions (~100 prompt files)
   - Main hub: `agent.system.main.md` connects everything

6. **Model Integration** - LiteLLM abstraction for multiple providers
   - Four types: Chat model, Utility model (summarization), Embedding model, Browser model
   - Configuration in `models.py` with ModelConfig dataclass
   - Streaming with real-time callbacks for UI
   - Rate limiting with configurable per-model limits

7. **Meta-Learning System** - Self-evolving prompt refinement (NEW in v0.9.7+)
   - Analyzes conversation patterns to identify improvements
   - Suggests prompt refinements based on failures and successes
   - Recommends new tools to build based on observed needs
   - Automatic versioning with rollback capabilities
   - Optional auto-apply mode for autonomous evolution
   - See `/docs/meta_learning/` directory for comprehensive guides

### Directory Structure (Key Paths)

```
/agentzero/
├── agent.py                    # Core Agent class, message loop entry (line 356)
├── models.py                   # LLM model config and integration
├── initialize.py               # Setup wizard
├── run_ui.py                   # Flask web server (main entry)
├── run_tunnel.py               # Remote access tunnel
│
├── /python/                    # Backend codebase
│   ├── /api/                   # 61+ Flask API endpoints
│   │   ├── message.py          # Main message processing API
│   │   ├── chat_*.py           # Chat management
│   │   ├── settings_*.py       # Settings endpoints
│   │   ├── memory_*.py         # Memory API
│   │   ├── projects.py         # Project management
│   │   └── ... (backup, file, knowledge, scheduler, etc.)
│   │
│   ├── /tools/                 # ~20 built-in tools
│   │   ├── code_execution_tool.py    # Python/Node/Shell execution
│   │   ├── call_subordinate.py       # Agent delegation
│   │   ├── memory_*.py               # Memory management
│   │   ├── search_engine.py          # SearXNG integration
│   │   ├── browser_agent.py          # Browser automation
│   │   ├── document_query.py         # Document RAG
│   │   ├── scheduler.py              # Task scheduling
│   │   ├── response.py               # Response finalization
│   │   ├── prompt_evolution.py       # Meta-learning analysis tool
│   │   └── ... (input, wait, notify, behaviour_adjustment, etc.)
│   │
│   ├── /extensions/            # 24 extension points
│   │   ├── agent_init/
│   │   ├── message_loop_start/
│   │   ├── before_main_llm_call/
│   │   ├── response_stream/
│   │   ├── message_loop_end/
│   │   ├── monologue_start/
│   │   ├── monologue_end/
│   │   └── ... (hist_add_tool_result, behaviour_adjustment, etc.)
│   │
│   └── /helpers/               # ~73 utility modules
│       ├── call_llm.py         # LLM interaction wrapper
│       ├── memory.py           # Vector DB memory system
│       ├── history.py          # Message history with compression
│       ├── tool.py             # Tool base class
│       ├── settings.py         # Settings management
│       ├── dotenv.py           # Environment configuration
│       ├── extract_tools.py    # Tool discovery from responses
│       ├── extension.py        # Extension loading system
│       ├── prompt_versioning.py # Prompt version control system
│       ├── mcp_handler.py      # MCP server/client support
│       ├── knowledge_import.py # Knowledge base management
│       ├── shell_*.py          # Shell execution (local, SSH)
│       ├── files.py            # File operations
│       ├── context.py          # Request context management
│       ├── log.py              # Logging system
│       └── ... (many more)
│
├── /webui/                     # Frontend (vanilla JS + Alpine.js)
│   ├── index.html              # Main page
│   ├── index.js                # App initialization
│   ├── /components/            # UI components (chat, sidebar, settings, etc.)
│   ├── /js/                    # JavaScript modules (api.js, messages.js, etc.)
│   ├── /css/                   # Stylesheets
│   └── /public/                # Static assets
│
├── /prompts/                   # ~100 system prompt files
│   ├── agent.system.main.md              # Central hub
│   ├── agent.system.main.role.md         # Agent role
│   ├── agent.system.main.communication.md
│   ├── agent.system.main.solving.md
│   ├── agent.system.tools.md             # Tool catalog
│   ├── agent.system.tool.*.md            # Individual tool instructions
│   ├── meta_learning.analyze.sys.md      # Meta-analysis prompt
│   ├── versioned/                        # Prompt version backups
│   │   ├── 20260105_143022/              # Timestamped snapshots
│   │   └── ... (automatic versioning)
│   └── ... (behaviour, memory, framework prompts)
│
├── /agents/                    # Agent profiles (configurations)
│   ├── default/                # Default configuration
│   ├── developer/              # Developer assistant profile
│   ├── researcher/             # Research assistant profile
│   ├── hacker/                 # Security/hacking profile
│   └── _example/               # Template for new profiles
│
├── /memory/                    # Persistent memory storage (FAISS indices)
│   ├── /default/               # Default agent memory
│   └── ... (user-specific subdirectories)
│
├── /knowledge/                 # Knowledge base for RAG
│   ├── /custom/                # User-provided knowledge
│   └── /default/               # Framework knowledge
│
├── /instruments/               # Custom automation scripts (tools users create)
│   ├── /custom/                # User-created instruments
│   └── /default/               # Framework instruments
│
├── /logs/                      # HTML chat logs (auto-generated per session)
│
├── /tests/                     # Test suite
│   ├── test_*.py               # Test files
│   └── ... (*_test.py files)
│
├── /docker/                    # Docker configuration
│   ├── /base/                  # Base image files
│   └── /run/                   # Runtime container configuration
│
├── /docs/                      # Documentation
│   ├── architecture.md
│   ├── installation.md
│   ├── usage.md
│   ├── development.md
│   ├── extensibility.md
│   ├── connectivity.md
│   ├── meta_learning.md        # Meta-learning system guide
│   └── ... (more detailed docs)
│
├── /conf/                      # Configuration files
│   └── model_providers.yaml    # Available LLM providers
│
├── requirements.txt            # Python dependencies
├── README.md                   # Project overview
└── LICENSE
```

## Core Concepts & Data Flow

### Message Loop (The Heartbeat)

The `Agent.monologue()` method in `agent.py:356` is the core event loop:

```
User Message → AgentContext.communicate()
  ↓
monologue() starts [OUTER LOOP: monologues]
  ├─ Extension: monologue_start
  ├─ [INNER LOOP: message iterations]
  │   ├─ Extension: message_loop_start
  │   ├─ Prepare system prompt + message history
  │   ├─ Extension: before_main_llm_call
  │   ├─ Call LLM (streaming with callbacks)
  │   │   ├─ Extension: reasoning_stream_*
  │   │   └─ Extension: response_stream_*
  │   ├─ Extract and execute tools from response
  │   │   └─ Add tool results to history
  │   └─ Extension: message_loop_end
  │   ├─ Repeat loop if tools returned (continue reasoning)
  │   └─ Break loop if response_tool was used
  ├─ Extension: monologue_end
  └─ Return final response to superior/user
  ↓
WebSocket stream to UI (real-time)
```

**Key principle:** The agent loops internally, using tools and getting results, until it explicitly uses `response_tool` to finalize and return.

### Tool Execution Flow

```
LLM response contains tool usage (e.g., "Tool name: code_execution_tool")
  ↓
extract_tools.py parses tool patterns from response
  ↓
Tool class dynamically imported from python/tools/[name].py
  ↓
Tool.before_execution() called (logging, display)
  ↓
Tool.execute() called (actual work happens)
  ↓
Tool.after_execution() called (post-processing)
  ↓
Result added to message history
  ↓
Message loop continues (agent reasons on result)
```

**Tool Base Class** in `python/helpers/tool.py`:
- `async execute()` - Main tool logic
- `async before_execution()` - Pre-execution hooks
- `async after_execution()` - Post-execution hooks

### Memory Flow

```
Conversation occurs
  ↓
Extensions capture important segments
  ↓
Utility LLM extracts and consolidates
  ↓
Store in memory areas (MAIN, FRAGMENTS, SOLUTIONS, INSTRUMENTS)
  ↓
Embed using sentence-transformers
  ↓
Index in FAISS vector database
  ↓
On next message: Semantic search retrieves relevant memories
  ↓
Memories loaded into context for agent
```

## Key Files & Classes

### Essential Files to Understand

| File | Purpose | Key Functions/Classes |
|------|---------|---------------------|
| `agent.py` | Core Agent logic | `Agent` class, `monologue()` method (line 356) |
| `models.py` | LLM integration | `ModelConfig` dataclass, model initialization |
| `run_ui.py` | Web server | Flask app setup, API route registration |
| `python/helpers/call_llm.py` | LLM interface wrapper | Streaming, token counting, rate limiting |
| `python/helpers/memory.py` | Vector memory system | FAISS integration, semantic search |
| `python/helpers/history.py` | Message history | Compression, bulk summarization, context mgmt |
| `python/helpers/tool.py` | Tool base class | Tool execution abstraction |
| `python/helpers/extract_tools.py` | Tool discovery | Parses LLM responses for tool patterns |
| `python/helpers/extension.py` | Extension system | Load and execute extensions in order |
| `python/helpers/settings.py` | Settings management | Persistent configuration |
| `python/helpers/context.py` | Request context | Agent context, logs, memory access |
| `python/helpers/prompt_versioning.py` | Prompt version control | Snapshots, rollback, version management |
| `python/tools/prompt_evolution.py` | Meta-learning tool | Analyzes patterns, suggests improvements |

### Extension Points (24 total)

Located in `python/extensions/` with numbered files. Common extension points:

- **Initialization:** `agent_init/`, `message_loop_start/`
- **LLM Interaction:** `before_main_llm_call/`, `response_stream/`
- **History:** `hist_add_tool_result/`, `hist_add_message/`
- **Behavior:** `behaviour_adjustment/`, `monologue_end/`
- **Special:** `mcp_handler/`, `knowledge_loading/`

### API Endpoints (61+ total)

**Main endpoints:**
- `POST /message` - Send message and stream response
- `POST /message_async` - Async message with attachments
- `GET/POST /settings_*` - Settings management
- `GET/POST /memory/*` - Memory API
- `POST /chat_*` - Chat management (create, load, remove, reset)
- `POST /backup_*` - Backup/restore functionality
- `POST /upload`, `GET /download_work_dir_file` - File operations
- `POST /synthesize` - Text-to-speech
- `POST /transcribe` - Speech-to-text
- `/projects/*` - Project management
- `/mcp/*`, `/rfc` - MCP integration

## Important Architectural Patterns

1. **Async-First Design** - Entire system uses async/await, non-blocking operations
2. **Extension Hooks** - 24+ customization points, numbered files execute in order
3. **Hierarchical Context** - Nested agent contexts with shared access to memory
4. **Tool-Based Abstraction** - No hard-coded capabilities; everything is a tool
5. **Prompt-Driven Behavior** - System prompts define all agent behavior (100+ files)
6. **Dynamic Composition** - Tools, prompts, extensions loaded at runtime
7. **Streaming Communication** - Real-time output via WebSocket to UI
8. **Vector Memory** - FAISS for semantic search of persistent knowledge
9. **Self-Evolution** - Meta-learning system learns from usage and refines prompts

## Configuration

### Environment Variables (.env)

```bash
# API Keys and credentials
OPENROUTER_API_KEY=...      # Default LLM provider
OPENAI_API_KEY=...          # For OpenAI models
ANTHROPIC_API_KEY=...       # For Claude models

# Server settings
HOST=localhost              # Default: localhost
PORT=50001                  # Default: 50001
SSL=false                   # Enable HTTPS

# Model selection
CHAT_MODEL_PROVIDER=openrouter
CHAT_MODEL_NAME=...
UTILITY_MODEL_PROVIDER=...
EMBEDDING_MODEL_PROVIDER=...

# Meta-learning configuration (optional)
ENABLE_PROMPT_EVOLUTION=false              # Enable self-evolution (default: false)
PROMPT_EVOLUTION_MIN_INTERACTIONS=20       # Min messages before analysis
PROMPT_EVOLUTION_MAX_HISTORY=100           # Max messages to analyze
PROMPT_EVOLUTION_CONFIDENCE_THRESHOLD=0.7  # Min confidence for suggestions
AUTO_APPLY_PROMPT_EVOLUTION=false          # Auto-apply high-confidence changes
PROMPT_EVOLUTION_TRIGGER_INTERVAL=10       # Monologues between auto-triggers
```

See `example.env` for complete configuration template with detailed comments.

### Model Configuration (conf/model_providers.yaml)

Defines available LLM providers:
- OpenAI, OpenRouter, Anthropic, Azure, local/custom
- Venice.ai, GitHub Copilot, and more
- Provider-specific settings

### Agent Profiles (agents/[profile]/)

Each profile can override:
- Prompts (in `prompts/` subfolder)
- Tools (selectively enabled/disabled)
- Memory subdirectory
- Behavior rules
- Settings defaults

## Security Considerations

- **Secrets Management** - Credentials stored separately, not leaked to prompts
- **CSRF Protection** - Token-based CSRF defense on all state-changing requests
- **Rate Limiting** - Per-model rate limits via LiteLLM
- **Code Sandboxing** - Code execution in isolated Docker containers
- **Session Management** - Cookie-based sessions with secure defaults
- **Loopback-only Default** - Web UI restricted to localhost unless configured
- **Login System** - Optional authentication for multi-user access

## Meta-Learning System (Self-Evolution)

Agent Zero includes a powerful meta-learning system that analyzes conversation patterns and evolves its prompts over time. This creates a feedback loop where the agent learns from experience and continuously improves.

### Key Features

- **Pattern Detection**: Identifies recurring failures and success patterns
- **Prompt Evolution**: Suggests specific refinements to system prompts
- **Tool Discovery**: Recommends new tools based on unmet needs
- **Gap Analysis**: Detects missing instructions and guidance
- **Automatic Versioning**: Creates snapshots before every change
- **Rollback Capability**: One-command restoration to any previous version
- **Auto-Apply Mode**: Optional autonomous application of high-confidence suggestions

### How It Works

1. **Accumulate History**: Agent interactions stored in message history
2. **Trigger Analysis**: Manual (prompt_evolution tool) or automatic (via extension)
3. **Meta-Analysis**: Utility LLM analyzes patterns using specialized prompt
4. **Generate Suggestions**: Structured JSON output with confidence scores
5. **Store Results**: Analysis saved in memory (SOLUTIONS area) for review
6. **Apply Changes**: Manual review or automatic application (configurable)
7. **Version Control**: Automatic snapshot before each change
8. **Continuous Learning**: Improved prompts benefit future interactions

### Components

**Core Files:**
- `python/tools/prompt_evolution.py` - Meta-analysis orchestration tool
- `python/helpers/prompt_versioning.py` - Version control system
- `prompts/meta_learning.analyze.sys.md` - Meta-analysis system prompt
- `prompts/versioned/` - Automatic prompt version backups

**Configuration:**
```bash
# Enable meta-learning
ENABLE_PROMPT_EVOLUTION=true

# Minimum interactions before analysis can run
PROMPT_EVOLUTION_MIN_INTERACTIONS=20

# Maximum history to analyze (token management)
PROMPT_EVOLUTION_MAX_HISTORY=100

# Confidence threshold for suggestions (0.0-1.0)
PROMPT_EVOLUTION_CONFIDENCE_THRESHOLD=0.7

# Auto-apply high-confidence changes (use with caution)
AUTO_APPLY_PROMPT_EVOLUTION=false
```

### Usage

**Manual Trigger (Recommended):**
```
User: Use the prompt_evolution tool to analyze recent interactions.

Agent: [Analyzes last 100 messages]

Meta-Learning Analysis Complete
Analyzed: 100 messages
Findings:
- 2 failure patterns identified
- 5 success patterns recognized
- 3 missing instructions detected
- 1 new tool suggested
- 4 prompt refinements proposed

Full analysis stored in memory (SOLUTIONS area)
Use memory_query to retrieve detailed suggestions
```

**Query Results:**
```
User: Query memory for meta-learning analysis.

Agent: [Retrieves from SOLUTIONS memory]

Recent Meta-Analysis (Monologue #42):
Failure Patterns:
- Agent uses 'find' instead of 'git grep' for code search (3 occurrences)
  Suggested refinement: agent.system.tool.code_exe.md

Prompt Refinements (confidence ≥ 0.7):
1. Add git grep guidance to code_execution_tool prompt (confidence: 0.85)
...
```

### Safety Features

1. **Automatic Versioning**: Every change creates a backup snapshot
2. **Confidence Scoring**: Only high-confidence suggestions considered
3. **Manual Review Mode**: Default requires human approval
4. **Rollback Capability**: One-command restoration to previous version
5. **Pattern Validation**: Minimum 2 occurrences required
6. **Metadata Tracking**: Full audit trail of all changes

### Version Management

**Create Manual Snapshot:**
```python
from python.helpers.prompt_versioning import create_prompt_backup
version_id = create_prompt_backup(label="before_major_change")
```

**List Versions:**
```python
from python.helpers.prompt_versioning import list_prompt_versions
versions = list_prompt_versions(limit=10)
```

**Rollback:**
```python
from python.helpers.prompt_versioning import rollback_prompts
rollback_prompts("20260105_143022")
```

### Best Practices

1. **Start Disabled**: Use agent for 50+ interactions before enabling
2. **Manual Review First**: Run 5-10 analyses in manual mode
3. **Validate Quality**: Test changes before enabling auto-apply
4. **Monitor Changes**: Check version history regularly
5. **Conservative Thresholds**: Start with confidence ≥ 0.8
6. **Gradual Evolution**: Apply 1-2 changes at a time

### Documentation

For comprehensive guide, see `/docs/meta_learning/README.md`:
- Detailed architecture
- Configuration profiles
- Usage patterns
- Troubleshooting
- Advanced customization
- API integration (planned)

---

## Extending Agent Zero

### Adding Custom Tools

1. Create `python/tools/my_tool.py`
2. Inherit from `Tool` base class in `python/helpers/tool.py`
3. Implement `async execute(self) -> Response`
4. Add prompt file `prompts/default/agent.system.tool.my_tool.md` to instruct the agent
5. Tool is auto-discovered when agent mentions it

### Adding Extensions

1. Create `python/extensions/[extension_point]/[priority]_name.py`
2. Implement `async extend(loop_data, ...)` function
3. Modify `loop_data` to change state/history/prompt
4. File name priority (10=early, 90=late) determines execution order

### Creating Agent Profiles

1. Copy `agents/_example/` to `agents/[new_profile]/`
2. Add custom prompts in `prompts/` subfolder
3. Can override default tools, settings, memory location
4. Select profile in settings or via API

### Custom Prompts

1. Copy prompts from `prompts/` to agent profile's `prompts/`
2. Modify text to change behavior
3. System loads agent profile prompts first, falls back to defaults
4. File naming follows convention: `agent.system.*.md`, `behaviour.*.md`, etc.

## Debugging & Troubleshooting

### Logs

- **Chat logs:** Auto-saved HTML files in `/logs/` directory
- **Server logs:** Printed to console, can redirect to file
- **Agent reasoning:** Visible in UI in real-time

### Common Issues

- **Tool not executing:** Check prompt includes tool instructions (`agent.system.tool.*.md`)
- **Memory not loading:** Verify embedding model is configured and FAISS index exists
- **LLM errors:** Check API key, rate limits, context window availability
- **UI not loading:** Ensure Flask server is running, check port bindings
- **Agent stuck:** Can intervene in real-time via UI or kill process

### Debug Mode

Enable verbose logging by modifying `python/helpers/log.py` or pass `--debug` flag if supported by entry point.

## Important Notes for Contributors

- All tool execution is async-based
- Prompts are extensible and not hard-coded
- Extensions should be minimal and focused
- Memory operations are async to avoid blocking
- API endpoints stream responses for real-time UI updates
- Message history includes both user and tool messages
- Context window management is automatic via history compression
- Do not hardcode behavior; use prompt-based configuration instead

## Documentation References

- Full architecture: `/docs/architecture.md`
- Installation guide: `/docs/installation.md`
- Usage guide: `/docs/usage.md`
- Development guide: `/docs/development.md`
- Extensibility guide: `/docs/extensibility.md`
- API connectivity: `/docs/connectivity.md`
- Meta-learning system: `/docs/meta_learning/README.md` (comprehensive guide)
- Troubleshooting: `/docs/troubleshooting.md`
