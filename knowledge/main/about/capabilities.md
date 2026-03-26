# Agent Zero - Capabilities Reference

## Code Execution

The agent can write and execute code in any language available in the Docker container. The execution environment is a Kali Linux container with two Python runtimes:
- `/opt/venv-a0` (Python 3.12) - the Agent Zero framework runtime
- `/opt/venv` (Python 3.13) - the agent's execution runtime (default for agent-run code)

The agent installs packages into the execution runtime (`/opt/venv`) via `pip install`. Packages needed by the framework itself must target `/opt/venv-a0`.

Supported runtimes for code execution: Python, Node.js, Bash/shell. Other languages (Go, Rust, PHP, etc.) can be used if the compiler/runtime is installed in the container.

Code runs in the terminal with real-time output streaming. Long-running processes, background jobs, and interactive sessions are supported. The agent can pause and resume code execution and interact with running processes.

## Terminal and System Operations

The agent has full root access to the Kali Linux Docker container. It can:
- Install packages via `apt`, `pip`, `npm`, and other package managers
- Create, read, write, move, and delete files anywhere in the container
- Run any system command, manage processes, set up services
- Access the network (HTTP requests, SSH, port scanning, etc.)
- Use Kali Linux security tools pre-installed in the container

## Skills (SKILL.md Standard)

Skills are structured markdown files that provide contextual expertise for specific tasks. When a skill is relevant to the current task, it is loaded into the agent's context and followed as a set of instructions. Skills are discovered from:
- `usr/skills/` (user-added skills)
- Project-scoped skills in `.a0proj/skills/`
- Skills imported via the web UI

Skills follow the open SKILL.md standard, making them portable across tools that support it. The agent executes skill instructions using `code_execution_tool` or `skills_tool`.

## Projects

Projects provide isolated workspaces with their own:
- Working directory (`usr/projects/<name>/`)
- Memory and knowledge scope
- Custom agent instructions (`.a0proj/agent.instructions.md`)
- Secrets and credentials (stored encrypted, not visible in agent context)
- MCP server configurations
- Git repository (can be cloned directly with authentication)

When a project is active, the agent's file operations, memory, and knowledge are scoped to that project. Projects prevent context bleed between separate work streams.

## Knowledge Base Access

The agent has automatic access to its knowledge base via similarity search. Knowledge is indexed from `knowledge/` (framework-level) and `usr/knowledge/<subdir>/` (user-level). The agent does not need to explicitly query knowledge - relevant content is surfaced automatically with memory recall. The `knowledge_tool` can also be called explicitly for targeted lookups.

## Multi-Agent Delegation

The agent can spawn subordinate agents with the `call_subordinate` tool. Subordinates can be given:
- Specific prompt profiles (`developer`, `researcher`, custom profiles)
- A defined role and task scope
- Access to the same tool set

Delegation is used to: parallelize work, maintain clean context per task, apply specialized profiles, and isolate long subtasks from the main context.

## Document Query

The `document_query_tool` can load and query arbitrary documents (local files or URLs) using a separate RAG pipeline. Unlike the knowledge base (which is pre-indexed), this tool indexes documents on demand with a configurable chunk size. Useful for analyzing large documents, codebases, or external content without polluting the persistent knowledge store.

## Scheduler

The agent can schedule tasks to run at specified times or intervals using the scheduler tool. Scheduled tasks run in the background with their own agent instances. Tasks are managed via the Scheduler UI in the web interface.

## External API and MCP

Agent Zero can act as both an MCP server and an MCP client:
- As an **MCP server**: exposes agent capabilities to other MCP-compatible clients
- As an **MCP client**: uses tools from external MCP servers (configured per project or globally)

An external REST API is available for programmatic task submission. Agent-to-Agent (A2A) protocol is supported for inter-system agent communication.

## Limitations

- **No persistent state between chats** unless explicitly memorized or saved to files.
- **Context window**: long conversations are summarized automatically, which can lose detail.
- **Memory recall is approximate**: similarity search may miss relevant memories or surface irrelevant ones.
- **No GUI interaction** outside the browser agent (which is separate from the main agent).
- **Container boundary**: the agent cannot affect systems outside the Docker container unless network access or volume mounts are configured.
- **Model capability ceiling**: tool usage quality and reasoning depth are bounded by the underlying LLM. Small models may struggle with complex multi-step tool use.
- **No real-time data** beyond web search. The agent's own knowledge cutoff is the underlying model's training cutoff.
