# Agent Zero - API Reference

All API handlers extend `ApiHandler` from `python/helpers/api.py`.
Handlers are auto-discovered from `python/api/` folder.
Each handler is mounted at `/{filename}` (e.g., `message.py` → `/message`).

## API Endpoints by Category

### Chat Management
| Endpoint | Methods | Auth | Purpose |
|----------|---------|------|---------|
| `/message` | POST | Auth+CSRF | Send message to agent |
| `/message_async` | POST | API Key | Async message (external API) |
| `/api_message` | POST | API Key | API message interface |
| `/chat_create` | POST | Auth+CSRF | Create new chat context |
| `/chat_load` | POST | Auth+CSRF | Load chat history |
| `/chat_reset` | POST | Auth+CSRF | Reset chat context |
| `/chat_remove` | POST | Auth+CSRF | Delete a chat |
| `/chat_export` | POST | Auth+CSRF | Export chat data |
| `/api_reset_chat` | POST | API Key | Reset chat via API |
| `/api_terminate_chat` | POST | API Key | Terminate chat via API |
| `/history_get` | POST | Auth+CSRF | Get conversation history |
| `/poll` | POST | Auth+CSRF | Poll for updates |
| `/nudge` | POST | Auth+CSRF | Nudge agent |
| `/pause` | POST | Auth+CSRF | Pause agent execution |

### Branding
| Endpoint | Methods | Auth | Purpose |
|----------|---------|------|---------|
| `/branding_get` | POST | None | Get brand configuration (name, slug, URL, GitHub URL) |

### Settings & Configuration
| Endpoint | Methods | Auth | Purpose |
|----------|---------|------|---------|
| `/settings_get` | POST | Auth+CSRF | Get current settings |
| `/settings_set` | POST | Auth+CSRF | Update settings |
| `/settings_workdir_file_structure` | POST | Auth+CSRF | Work directory structure |

### File Management
| Endpoint | Methods | Auth | Purpose |
|----------|---------|------|---------|
| `/upload` | POST | Auth+CSRF | Upload files |
| `/upload_work_dir_files` | POST | Auth+CSRF | Upload to work directory |
| `/get_work_dir_files` | POST | Auth+CSRF | List work directory files |
| `/download_work_dir_file` | POST | Auth+CSRF | Download work directory file |
| `/edit_work_dir_file` | POST | Auth+CSRF | Edit work directory file |
| `/delete_work_dir_file` | POST | Auth+CSRF | Delete work directory file |
| `/rename_work_dir_file` | POST | Auth+CSRF | Rename work directory file |
| `/file_info` | POST | Auth+CSRF | Get file metadata |
| `/image_get` | POST | Auth+CSRF | Get image data |

### Memory & Knowledge
| Endpoint | Methods | Auth | Purpose |
|----------|---------|------|---------|
| `/memory_dashboard` | POST | Auth+CSRF | Memory analytics dashboard |
| `/knowledge_path_get` | POST | Auth+CSRF | Get knowledge base path |
| `/knowledge_reindex` | POST | Auth+CSRF | Reindex knowledge base |
| `/import_knowledge` | POST | Auth+CSRF | Import knowledge files |

### Agent Management
| Endpoint | Methods | Auth | Purpose |
|----------|---------|------|---------|
| `/agents` | POST | Auth+CSRF | CRUD for agent profiles |
| `/subagents` | POST | Auth+CSRF | Manage subordinate agents |
| `/ctx_window_get` | POST | Auth+CSRF | Get context window info |
| `/api_log_get` | POST | Auth+CSRF | Get agent logs |
| `/api_files_get` | POST | Auth+CSRF | Get agent files |

### Scheduler
| Endpoint | Methods | Auth | Purpose |
|----------|---------|------|---------|
| `/scheduler_tasks_list` | POST | Auth+CSRF | List scheduled tasks |
| `/scheduler_task_create` | POST | Auth+CSRF | Create task |
| `/scheduler_task_update` | POST | Auth+CSRF | Update task |
| `/scheduler_task_delete` | POST | Auth+CSRF | Delete task |
| `/scheduler_task_run` | POST | Auth+CSRF | Run task immediately |
| `/scheduler_tick` | POST | Auth+CSRF | Tick the scheduler |

### MCP Server Management
| Endpoint | Methods | Auth | Purpose |
|----------|---------|------|---------|
| `/mcp_servers_status` | POST | Auth+CSRF | Get MCP server status |
| `/mcp_servers_apply` | POST | Auth+CSRF | Apply MCP config |
| `/mcp_server_get_detail` | POST | Auth+CSRF | Get MCP server details |
| `/mcp_server_get_log` | POST | Auth+CSRF | Get MCP server logs |

### Notifications
| Endpoint | Methods | Auth | Purpose |
|----------|---------|------|---------|
| `/notification_create` | POST | Auth+CSRF | Create notification |
| `/notifications_history` | POST | Auth+CSRF | Get notification history |
| `/notifications_mark_read` | POST | Auth+CSRF | Mark notifications read |
| `/notifications_clear` | POST | Auth+CSRF | Clear notifications |

### Backup & Restore
| Endpoint | Methods | Auth | Purpose |
|----------|---------|------|---------|
| `/backup_create` | POST | Auth | Create backup |
| `/backup_restore` | POST | Auth | Restore from backup |
| `/backup_restore_preview` | POST | Auth | Preview restore |
| `/backup_inspect` | POST | Auth | Inspect backup file |
| `/backup_test` | POST | Auth | Test backup patterns |
| `/backup_get_defaults` | POST | Auth | Get default backup config |
| `/backup_preview_grouped` | POST | Auth | Preview grouped backup |

### Skills & Projects
| Endpoint | Methods | Auth | Purpose |
|----------|---------|------|---------|
| `/skills` | POST | Auth+CSRF | Manage skills |
| `/skills_import` | POST | Auth+CSRF | Import skills |
| `/skills_import_preview` | POST | Auth+CSRF | Preview skill import |
| `/projects` | POST | Auth+CSRF | Manage projects |

### Infrastructure
| Endpoint | Methods | Auth | Purpose |
|----------|---------|------|---------|
| `/health` | GET | None | Health check |
| `/csrf_token` | POST | Auth | Get CSRF token |
| `/restart` | POST | Auth+CSRF | Restart server |
| `/tunnel` | POST | Auth+CSRF | Tunnel management |
| `/tunnel_proxy` | POST | Auth+CSRF | Tunnel proxy |
| `/banners` | POST | Auth+CSRF | Get UI banners |
| `/synthesize` | POST | Auth+CSRF | TTS synthesis |
| `/transcribe` | POST | Auth+CSRF | STT transcription |
| `/rfc` | POST | Auth+CSRF | RFC exchange |
| `/message_queue_add/send/remove` | POST | Auth+CSRF | Message queue ops |

### Auth
| Endpoint | Methods | Auth | Purpose |
|----------|---------|------|---------|
| `/login` | GET,POST | None | Login page + handler |
| `/logout` | GET | None | Logout handler |
