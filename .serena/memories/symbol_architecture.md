# Agent Zero Symbol Architecture & Key Classes

## Core Classes and Symbols

### Main Framework Classes
- **Agent** - Core agent implementation
- **AgentConfig** - Agent configuration structure
- **AgentContext** - Runtime context management
- **AgentContextType** - Context type definitions

### Model Management
- **ModelConfig** - Model configuration class
- **ModelType** - Model type enumeration
- **LiteLLMChatWrapper** - LiteLLM integration
- **LocalSentenceTransformerWrapper** - Local embeddings
- **ChatGenerationResult** - Chat response structure
- **ChatChunk** - Streaming chat chunks

### Tool System
- **Base Tool Class** - Parent class for all tools
- **CodeExecution** - Code execution tool
- **MemorySave** - Memory persistence tool
- **CallSubordinate** - Agent delegation tool
- **BrowserAgent** - Browser automation tool
- **SearchEngine** - Web search tool

### Message Handling
- **UserMessage** - User input structure
- **LoopData** - Conversation loop data
- **HandledException** - Controlled error handling
- **InterventionException** - User intervention

### Helper Classes
- **ShellWrap** - Shell command wrapper
- **State** - State management
- **PrintStyle** - Output formatting
- **RateLimiter** - API rate limiting

## Symbol Patterns

### Tool Implementation Pattern
```python
class ToolName:
    def __init__(self, agent, args):
        # Tool initialization
    
    def execute(self):
        # Tool execution logic
        return result
```

### Model Configuration Pattern
```python
ModelConfig(
    type=ModelType.CHAT,
    provider="provider_name",
    name="model_name",
    api_base="url",
    ctx_length=context_length,
    kwargs=additional_params
)
```

### Agent Hierarchy Pattern
```
Agent 0 (User Interface)
    ├── Agent 1 (Delegated Task)
    │   ├── Agent 1.1 (Subtask)
    │   └── Agent 1.2 (Subtask)
    └── Agent 2 (Delegated Task)
```

## Key Symbol Relationships

### Agent → Tools
- Agent instances create and execute tools
- Tools receive agent context for operations
- Tools can spawn subordinate agents

### Agent → Memory
- Agents persist data via MemorySave
- Agents retrieve data via MemoryLoad
- Memory organized by areas and keys

### Agent → Models
- Agents use chat models for reasoning
- Agents use utility models for tasks
- Agents use embedding models for knowledge

### Tools → Helpers
- Tools use helpers for specific operations
- Shell tools use ShellWrap for execution
- Browser tools use Playwright integration

## Symbol Discovery Methods

### Finding Classes
```python
# Search for class definitions
pattern: "^class \\w+"

# Get class methods
find_symbol with depth=1

# Find class references
find_referencing_symbols
```

### Tool Discovery
- Tools auto-discovered from `/python/tools/`
- Disabled tools have `._py` extension
- Each tool is standalone class

### Configuration Symbols
- Settings merged from defaults
- Environment variables override
- Project-specific configurations

## Common Symbol Operations

### Creating New Tool
1. Add class to `/python/tools/`
2. Inherit from Tool base
3. Implement execute method
4. Tool auto-discovered

### Extending Agent
1. Modify AgentConfig
2. Update initialization
3. Adjust prompts
4. Add capabilities

### Memory Operations
- Save: `memory.save(key, value, area)`
- Load: `memory.load(key, area)`
- Delete: `memory.delete(key, area)`
- Search: `memory.search(query)`

## Symbol Naming Conventions

### Python Symbols
- Classes: PascalCase (Agent, ModelConfig)
- Functions: snake_case (initialize_agent, execute_tool)
- Constants: UPPER_SNAKE_CASE
- Private: _leading_underscore

### Configuration Keys
- Nested with underscores: chat_model_name
- Uppercase in .env: CHAT_MODEL_NAME
- Lowercase in settings dict

### Memory Keys
- Descriptive strings
- Area-based organization
- Project-scoped isolation

## Important Symbol Locations

### Entry Points
- `agent.py`: Agent class
- `initialize.py`: initialize_agent()
- `run_ui.py`: Web UI entry
- `run_cli.py`: CLI entry

### Core Logic
- `/python/helpers/call_llm.py`: LLM interaction
- `/python/helpers/memory.py`: Memory system
- `/python/helpers/tool.py`: Tool base class
- `/python/helpers/projects.py`: Project management

### Integration Points
- `/python/api/`: Web API endpoints
- `/python/helpers/mcp_handler.py`: MCP protocol
- `/python/helpers/docker.py`: Container integration