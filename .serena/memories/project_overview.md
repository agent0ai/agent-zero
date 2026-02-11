# Agent Zero - Project Overview

## Purpose
Agent Zero is a personal, organic agentic AI framework that grows and learns with the user. It is a general-purpose AI assistant that uses the computer as a tool—writing code, executing terminal commands, browsing the web, managing memory, and cooperating with subordinate agent instances.

## Tech Stack
- **Language**: Python 3 (primary), JavaScript/HTML/CSS (web UI)
- **Web Framework**: Flask (sync routes) + uvicorn (ASGI) + python-socketio (WebSocket)
- **LLM Integration**: LiteLLM (multi-provider), LangChain Core
- **Embeddings**: sentence-transformers, FAISS (vector DB)
- **Browser Automation**: Playwright, browser-use
- **Search**: DuckDuckGo, SearXNG, Perplexity
- **Document Processing**: unstructured, pypdf, pymupdf, newspaper3k
- **MCP**: fastmcp for server, mcp SDK for client
- **Scheduling**: crontab
- **Docker**: Custom base image + DockerfileLocal for local dev
- **Testing**: pytest, pytest-asyncio, pytest-mock

## Architecture
- `agent.py` — Core Agent and AgentContext classes
- `models.py` — LLM model configuration using LiteLLM
- `initialize.py` — Agent initialization and config management
- `run_ui.py` — Flask/uvicorn web server entry point
- `python/tools/` — Agent tools (code execution, memory, search, browser, etc.)
- `python/helpers/` — Utility modules (files, docker, SSH, memory, MCP, etc.)
- `python/api/` — REST API endpoint handlers (auto-discovered from folder)
- `python/websocket_handlers/` — WebSocket event handlers (namespace-based discovery)
- `python/extensions/` — Hook/extension points for the agent loop lifecycle
- `prompts/` — System prompts and message templates (Markdown/Python)
- `webui/` — Frontend HTML/CSS/JS (vanilla, no framework)
- `knowledge/` — Knowledge base files for RAG
- `skills/` — SKILL.md standard skills (portable agent capabilities)
- `tests/` — pytest test suite
- `docker/` — Docker build scripts (base image + run scripts)
- `conf/` — Configuration files

## Key Design Patterns
- **Extension system**: Lifecycle hooks in `python/extensions/` directories (e.g., `message_loop_start`, `tool_execute_before`)
- **Auto-discovery**: Tools, API handlers, and WebSocket handlers are auto-loaded from their folders
- **Multi-agent**: Agents can spawn subordinate agents; the first agent's superior is the human user
- **Memory**: Persistent vector-DB-based memory with FAISS
- **Prompt-driven**: Behavior is defined by prompts in `prompts/` folder, fully customizable
