# Apollos AI - Tools Reference

All tools extend the base `Tool` class from `python/helpers/tool.py`.
Tools are auto-discovered from `python/tools/` (files ending in `._py` are disabled).

## Tool Catalog (19 active tools)

### Code Execution
| Tool | File | Purpose |
|------|------|---------|
| `code_execution_tool` | code_execution_tool.py | Terminal/Python/Node.js execution with multi-session support |
| `input` | input.py | Forward keyboard input to code execution sessions |

### Memory
| Tool | File | Purpose |
|------|------|---------|
| `memory_load` | memory_load.py | Semantic search in FAISS vector memory (threshold, limit, filter) |
| `memory_save` | memory_save.py | Save text to vector memory with metadata |
| `memory_delete` | memory_delete.py | Delete memories by comma-separated IDs |
| `memory_forget` | memory_forget.py | Delete memories by semantic query match |

### Communication
| Tool | File | Purpose |
|------|------|---------|
| `response` | response.py | Return final response to user (breaks loop) |
| `call_subordinate` | call_subordinate.py | Delegate tasks to subordinate agents |
| `a2a_chat` | a2a_chat.py | Communicate with external A2A agents |
| `notify_user` | notify_user.py | Send UI notifications (info/warning/error/success) |

### Browser
| Tool | File | Purpose |
|------|------|---------|
| `browser_agent` | browser_agent.py | Automated browser control via Playwright/browser-use |
| `vision_load` | vision_load.py | Load/optimize images for vision tasks |

### Search & Knowledge
| Tool | File | Purpose |
|------|------|---------|
| `search_engine` | search_engine.py | Web search via SearXNG |
| `document_query` | document_query.py | Query documents via vector similarity |

### Skills & Scheduling
| Tool | File | Purpose |
|------|------|---------|
| `skills_tool` | skills_tool.py | List/load SKILL.md-standard skills |
| `scheduler` | scheduler.py | Create/manage scheduled, adhoc, and planned tasks |

### Behavior & Flow
| Tool | File | Purpose |
|------|------|---------|
| `behaviour_adjustment` | behaviour_adjustment.py | Dynamically adjust agent behavior rules |
| `wait` | wait.py | Pause execution (duration or timestamp) |
| `unknown` | unknown.py | Handle unrecognized tool calls with helpful feedback |

## Disabled Tools (._py suffix)
- `browser_do._py`, `browser._py`, `browser_open._py`, `knowledge_tool._py`
