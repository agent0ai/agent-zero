# Agent Zero - Internal Architecture

## The Agent Loop (Monologue Cycle)

Each agent runs a continuous monologue loop. On each cycle the agent receives its current context (system prompt + message history), produces a JSON response (thoughts, headline, tool name, tool args), and the framework executes the named tool. The tool result is appended to history and the loop continues until the agent calls `response` to deliver a final answer to its superior.

The loop handles: message history management, context window limits (via summarization), memory recall injection, intervention from superiors, and error recovery (misformat retries, tool-not-found handling).

## Context and State

`AgentContext` (defined in `agent.py`) is the central state container for a conversation. It holds:
- Agent number and identifier
- Message history
- The active agent profile and prompt configuration
- Reference to memory, knowledge, and tool systems
- Project context if a project is active
- `extras` dict - additional content injected into the system prompt each turn (memories, solutions, agent info, workdir structure)

Each WebSocket session connects to one `AgentContext`. Multiple concurrent chats run in separate contexts. The framework is initialized in `initialize.py` and the server entry point is `run_ui.py`.

## Prompt Assembly

System prompts are assembled from fragment files on each loop iteration. The main system prompt is `prompts/agent.system.main.md`, which includes sub-prompts via `{{ include "filename.md" }}` directives. Agent profiles (in `agents/<profile>/prompts/`) can override individual fragments. This means a subordinate with the `developer` profile gets a different role and communication section while sharing the same tool list and solving workflow as the base agent.

Prompt fragments are in `prompts/`. Plugin system prompts are in `plugins/<plugin>/prompts/`. The assembled system prompt is dynamic - it changes based on profile, active project, loaded tools, recalled memories, and injected extras.

## Multi-Agent Hierarchy

The hierarchy is a tree with the human user at the root. Each node is an agent instance running in its own context. A superior calls `call_subordinate` with a message and optional profile name; this creates a new `AgentContext` and runs the subordinate agent's loop until it returns a response.

Agent 0 is always the top-level agent whose superior is the user. When Agent 0 delegates a task to a subordinate, that subordinate can itself delegate further. There is no enforced depth limit. Agents share the same tool system but each has its own isolated context and history.

Subordinates can be given specific prompt profiles (`developer`, `researcher`, or any custom profile in `agents/`). Profiles change the role, communication style, and available instructions without changing the underlying framework.

## Memory and Knowledge Pipeline

### Knowledge (vector DB, read-only)
Knowledge files (in `knowledge/` and `usr/knowledge/`) are loaded at startup, embedded, and stored in a FAISS vector index per memory subdir. Files are tracked by checksum; only changed files are re-indexed. Supported formats: `.md`, `.txt`, `.pdf`, `.csv`, `.html`, `.json`.

The memory areas are:
- `main` - general knowledge and facts (files in knowledge root or `main/` subdir)
- `fragments` - partial or supplementary knowledge
- `solutions` - known solutions to problems

### Recall (automatic, per conversation turn)
The `RecallMemories` extension runs every N loop iterations (configurable). It queries the vector store using either the raw conversation or a utility-LLM-generated search query. Results from `main` and `fragments` areas plus `solutions` are injected into `loop_data.extras_persistent`, which gets rendered into the system prompt via `agent.context.extras.md` template.

The agent sees recalled memories as a section in its system prompt labeled "Memories on the topic". The agent is instructed not to over-rely on them.

### Agent memory (read-write, via memorize tool)
The agent can explicitly save facts, solutions, and code snippets using the `memorize` tool. These are stored in the same FAISS index under the `main` or `solutions` area and recalled in future conversations. Memory can also be consolidated (summarized) and managed through the Memory Dashboard in the web UI.

## Tool System

Tools are Python classes in `python/tools/` that inherit from `Tool`. Each tool implements an `execute()` async method. Tools are discovered at startup and registered in the agent's tool list (rendered into the system prompt as `{{tools}}`). The agent names a tool in its JSON response; the framework finds and calls it.

Plugin tools can be added in `plugins/<plugin>/tools/` or `usr/plugins/<plugin>/tools/` without modifying core files.

## Extension and Plugin System

The plugin system (`python/helpers/plugins.py`) discovers plugins from `plugins/` and `usr/plugins/`. Each plugin has a `plugin.yaml` manifest declaring name, version, and settings. Plugins can contribute: API handlers, tools, WebUI components, extensions, and hooks. User plugins in `usr/plugins/` are never overwritten by framework updates. The agent has skills to create, manage, debug, review and contribute plugins to the Plugin Index repository (https://github.com/agent0ai/a0-plugins)

## Frontend Architecture

The web UI is built with Alpine.js and ES module components. The main shell is `webui/index.html`. Components are in `webui/components/`. Frontend state is managed via Alpine stores defined with `createStore` from `/js/AlpineStore.js`.

Real-time communication uses Socket.io WebSockets via a unified `/ws` namespace. WebSocket handlers (WsHandler subclasses) are in `api/ws_*.py`. The connection manager is in `helpers/ws_manager.py`. API handlers are in `api/`, each deriving from `ApiHandler` in `helpers/api.py`.
