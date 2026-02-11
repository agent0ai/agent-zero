# Agent Zero - Helpers Reference (84 modules)

## Grouped by Functional Area

### Memory & Knowledge (5)
| Module | Purpose |
|--------|---------|
| `memory.py` | Vector-backed memory system with FAISS |
| `vector_db.py` | FAISS wrapper with LocalFileStore cache |
| `memory_consolidation.py` | Memory compression and summarization |
| `knowledge_import.py` | Bulk knowledge base import/indexing |
| `document_query.py` | Query documents using vector similarity |

### LLM Integration (6)
| Module | Purpose |
|--------|---------|
| `call_llm.py` | High-level LLM invocation helpers |
| `tokens.py` | Token counting (tiktoken cl100k_base) with 1.1x buffer |
| `rate_limiter.py` | Sliding window rate limiting per provider/model |
| `providers.py` | Provider configuration registry |
| `browser_use_monkeypatch.py` | Compatibility patches for browser-use |
| `dotenv.py` | .env loading with validation (see `docs/reference/environment-variables.md`) |

### Shell & Execution (5)
| Module | Purpose |
|--------|---------|
| `shell_local.py` | Local shell via TTY session |
| `shell_ssh.py` | Remote SSH via Paramiko |
| `docker.py` | Docker container lifecycle management |
| `tty_session.py` | Terminal emulation (pty-based) |
| `runtime.py` | Runtime utilities (terminal detection, bin lookup, port config) |

### Chat Persistence (3)
| Module | Purpose |
|--------|---------|
| `persist_chat.py` | Chat serialization to `usr/chats/{id}/` |
| `history.py` | Message history with topic-based compression |
| `message_queue.py` | Async message queue for inter-agent communication |

### Browser Automation (3)
| Module | Purpose |
|--------|---------|
| `browser_use.py` | browser-use library wrapper |
| `playwright.py` | Direct Playwright integration |
| `browser.py` | Generic browser interface |

### MCP Integration (2)
| Module | Purpose |
|--------|---------|
| `mcp_handler.py` | MCP client (connect to external MCP servers) |
| `mcp_server.py` | MCP server (expose Agent Zero as MCP, FastMCP + SSE) |

### Configuration (5)
| Module | Purpose |
|--------|---------|
| `settings.py` | Global settings (env override via A0_SET_* prefix) |
| `projects.py` | Multi-project management |
| `secrets.py` | Secrets manager with streaming filter |
| `security.py` | Filename sanitization, security helpers |
| `branding.py` | Centralized brand config (BRAND_NAME, BRAND_SLUG, BRAND_URL, BRAND_GITHUB_URL) |

### Skills (3)
| Module | Purpose |
|--------|---------|
| `skills.py` | Skill discovery, loading, YAML metadata parsing |
| `skills_import.py` | Skill import/installation |
| `skills_cli.py` | CLI interface for skills |

### Logging & Monitoring (6)
| Module | Purpose |
|--------|---------|
| `log.py` | Structured logging (types: log/success/warning/error/hint/progress) |
| `state_monitor.py` | State change monitoring |
| `state_monitor_integration.py` | Integration hooks for state monitor |
| `state_snapshot.py` | Snapshot capture for debugging |
| `print_style.py` | Terminal output styling (colors, padding) |
| `print_catch.py` | Print output interception |

### WebSocket (3)
| Module | Purpose |
|--------|---------|
| `websocket.py` | WebSocketHandler base class, origin validation |
| `websocket_manager.py` | Event routing, connection tracking, buffering |
| `websocket_namespace_discovery.py` | Auto-discover handlers from folder structure |

### Communication (5)
| Module | Purpose |
|--------|---------|
| `email_client.py` | Email client (IMAP) |
| `notification.py` | Push notification system |
| `rfc.py` / `rfc_exchange.py` / `rfc_files.py` | RFC-based data exchange |

### Search (3)
| Module | Purpose |
|--------|---------|
| `duckduckgo_search.py` | DuckDuckGo search |
| `perplexity_search.py` | Perplexity AI search |
| `searxng.py` | SearXNG meta-search |

### File Utilities (4)
| Module | Purpose |
|--------|---------|
| `files.py` | File I/O, path resolution, placeholder replacement |
| `file_tree.py` | Directory tree visualization |
| `file_browser.py` | File browsing with security |
| `attachment_manager.py` | Attachment handling |

### Data Processing (5)
| Module | Purpose |
|--------|---------|
| `dirty_json.py` | Lenient JSON parsing for LLM outputs |
| `crypto.py` | Encryption/decryption utilities |
| `guids.py` | UUID generation |
| `strings.py` | String manipulation helpers |
| `images.py` | Image processing |

### Infrastructure (10)
| Module | Purpose |
|--------|---------|
| `api.py` | ApiHandler base class |
| `tool.py` | Tool base class |
| `extension.py` | Extension base class + `call_extensions()` |
| `extract_tools.py` | Dynamic class loading from folders |
| `context.py` | ContextVar-based async context data |
| `defer.py` | DeferredTask for async execution |
| `errors.py` | Error types (RepairableException, HandledException) |
| `process.py` | Process management |
| `subagents.py` | Agent hierarchy path resolution |
| `localization.py` | Multi-language support |

### Other (8)
| Module | Purpose |
|--------|---------|
| `backup.py` | BackupService for data export/import |
| `migration.py` | Data migration between versions |
| `update_check.py` | Version update checking |
| `login.py` | Authentication credential management |
| `git.py` | Git info extraction |
| `tunnel_manager.py` | Cloudflare tunnel management |
| `task_scheduler.py` | Cron-based task scheduling |
| `job_loop.py` | Background job execution loop |
| `kokoro_tts.py` | TTS via Kokoro |
| `whisper.py` | STT via Whisper |
| `fasta2a_client.py` / `fasta2a_server.py` | A2A protocol support |
| `wait.py` | Wait/sleep utilities |
