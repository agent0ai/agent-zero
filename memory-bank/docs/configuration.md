# Configuration

> **Navigation:** [Index](./index.md) | [Architecture](./architecture.md) | [Agent Profiles](./agent-profiles.md) | [Tools](./tools.md) | [Extensions](./extensions.md) | [Prompt System](./prompt-system.md) | [Memory & Skills](./memory-and-skills.md)

---

## Settings Hierarchy

Settings are resolved in priority order (highest wins):

```
5. Environment variables:  A0_SET_<key>=value        ← highest priority
4. Runtime CLI args:       python run_ui.py --key=value
3. Profile settings:       agents/<profile>/settings.json
2. User settings:          usr/settings.json
1. Hardcoded defaults:     python/helpers/settings.py  ← lowest priority
```

The UI Settings panel writes to `usr/settings.json`. Profile-specific overrides in `agents/<profile>/settings.json` are merged on top when that profile is active.

**Implementation:** `python/helpers/settings.py`

---

## Environment Variable Overrides

Any setting can be overridden via environment variable. Format: `A0_SET_<SETTING_NAME>=<value>` (case-insensitive).

```bash
# Set chat model
A0_SET_chat_model_name="anthropic/claude-opus-4.6"

# Enable hacker profile on container start
A0_SET_agent_profile=hacker

# Set shell to local (inside Docker)
A0_SET_shell_interface=local

# JSON values
A0_SET_chat_model_kwargs='{"temperature": 0.7}'
A0_SET_litellm_global_kwargs='{"timeout": 30}'
```

---

## Model Settings

Agent Zero uses four distinct model roles, each with independent provider/name/limit configuration.

### Chat Model

The primary LLM for agent reasoning and tool calls.

| Setting | Default | Description |
|---------|---------|-------------|
| `chat_model_provider` | `openrouter` | LLM provider |
| `chat_model_name` | `anthropic/claude-sonnet-4.6` | Model name |
| `chat_model_api_base` | `""` | Custom API endpoint (optional) |
| `chat_model_kwargs` | `{}` | Extra kwargs passed to LiteLLM |
| `chat_model_ctx_length` | `100000` | Context window size in tokens |
| `chat_model_ctx_history` | `0.7` | Fraction of context used for history |
| `chat_model_vision` | `true` | Enables vision/multimodal input |
| `chat_model_rl_requests` | `0` | Rate limit: requests/min (0 = unlimited) |
| `chat_model_rl_input` | `0` | Rate limit: input tokens/min |
| `chat_model_rl_output` | `0` | Rate limit: output tokens/min |

### Utility Model

Lightweight LLM for background operations (memory summarization, keyword extraction, chat renaming, behavior rule merging).

| Setting | Default | Description |
|---------|---------|-------------|
| `util_model_provider` | `openrouter` | Provider |
| `util_model_name` | `google/gemini-3-flash-preview` | Model name |
| `util_model_api_base` | `""` | Custom endpoint |
| `util_model_ctx_length` | `100000` | Context window |
| `util_model_ctx_input` | `0.7` | Fraction used for input |
| `util_model_kwargs` | `{}` | Extra kwargs |
| `util_model_rl_requests` | `0` | Rate limits |
| `util_model_rl_input` | `0` | |
| `util_model_rl_output` | `0` | |

### Embedding Model

Generates vector embeddings for FAISS memory. Uses SentenceTransformers (local, no API key required) by default.

| Setting | Default | Description |
|---------|---------|-------------|
| `embed_model_provider` | `huggingface` | Provider |
| `embed_model_name` | `sentence-transformers/all-MiniLM-L6-v2` | Model name |
| `embed_model_api_base` | `""` | Custom endpoint |
| `embed_model_kwargs` | `{}` | Extra kwargs |
| `embed_model_rl_requests` | `0` | Rate limits |
| `embed_model_rl_input` | `0` | |

### Browser Model

Vision-capable LLM used by `browser_agent` to analyze screenshots.

| Setting | Default | Description |
|---------|---------|-------------|
| `browser_model_provider` | `openrouter` | Provider |
| `browser_model_name` | `anthropic/claude-sonnet-4.6` | Model name |
| `browser_model_api_base` | `""` | Custom endpoint |
| `browser_model_vision` | `true` | Must be true for browser use |
| `browser_model_kwargs` | `{}` | Extra kwargs |
| `browser_http_headers` | `{}` | Custom HTTP headers for browser requests |
| `browser_model_rl_requests` | `0` | Rate limits |
| `browser_model_rl_input` | `0` | |
| `browser_model_rl_output` | `0` | |

---

## LLM Provider Configuration

Providers are configured in `conf/model_providers.yaml` (21 chat providers, 9 embedding providers).

### Common providers

| Provider key | Service |
|-------------|---------|
| `openrouter` | OpenRouter (aggregates 200+ models) |
| `anthropic` | Anthropic direct API |
| `openai` | OpenAI direct API |
| `azure` | Azure OpenAI |
| `google` | Google AI Studio |
| `ollama` | Local Ollama instance |
| `lmstudio` | Local LM Studio |
| `huggingface` | HuggingFace (embeddings) |
| `groq` | Groq (fast inference) |
| `mistral` | Mistral AI |

### API Keys

API keys are loaded from environment variables or `.env` file, NOT stored in `usr/settings.json`.

**Format in `.env`:**
```bash
API_KEY_OPENROUTER=sk-or-xxx
API_KEY_ANTHROPIC=sk-ant-xxx
API_KEY_OPENAI=sk-xxx
API_KEY_GOOGLE=AIzaXXX
```

For OpenRouter, a single key provides access to all supported models.

**Multiple keys (round-robin):** Separate with commas:
```bash
API_KEY_OPENROUTER=sk-or-key1,sk-or-key2,sk-or-key3
```

**NVD API key** (optional, for `cve_lookup` tool higher rate limits):
```bash
NVD_API_KEY=your-nvd-api-key
```

---

## Agent Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `agent_profile` | `"agent0"` | Active profile: `agent0`, `hacker`, `developer`, `researcher`, `default` |
| `agent_memory_subdir` | `"default"` | FAISS memory subdirectory name |
| `agent_knowledge_subdir` | `"custom"` | Knowledge base subdirectory name |

**Hacker profile `settings.json`:**
```json
{
  "agent_profile": "hacker",
  "agent_memory_subdir": "hacker",
  "workdir_path": "usr/workdir",
  "memory_recall_enabled": true,
  "memory_memorize_enabled": true
}
```

The `agent_memory_subdir: "hacker"` isolates the hacker agent's FAISS index from other profiles.

---

## Working Directory Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `workdir_path` | `"usr/workdir"` | Base working directory path |
| `workdir_show` | `true` | Include directory tree in system prompt |
| `workdir_max_depth` | `5` | Max directory depth to show |
| `workdir_max_files` | `20` | Max files per directory |
| `workdir_max_folders` | `20` | Max folders per directory |
| `workdir_max_lines` | `250` | Max lines of tree to show |
| `workdir_gitignore` | *(patterns)* | Patterns to exclude from tree display |

---

## Memory Recall

| Setting | Default | Description |
|---------|---------|-------------|
| `memory_recall_enabled` | `true` | Enable automatic memory recall |
| `memory_recall_delayed` | `false` | Delay recall until after first response |
| `memory_recall_interval` | `3` | Recall every N message loop iterations |
| `memory_recall_history_len` | `10000` | Characters of history used for recall query |
| `memory_recall_memories_max_search` | `12` | Max memories to search |
| `memory_recall_solutions_max_search` | `8` | Max solutions to search |
| `memory_recall_memories_max_result` | `5` | Top memories returned |
| `memory_recall_solutions_max_result` | `3` | Top solutions returned |
| `memory_recall_similarity_threshold` | `0.7` | Min cosine similarity (0–1) |
| `memory_recall_query_prep` | `false` | Pre-process query via utility LLM |
| `memory_recall_post_filter` | `false` | Post-filter results via utility LLM |
| `memory_memorize_enabled` | `true` | Enable automatic memorization |
| `memory_memorize_consolidation` | `true` | Merge similar memories via utility LLM |
| `memory_memorize_replace_threshold` | `0.9` | Replace existing memory if similarity > 0.9 |

---

## Shell & Code Execution

| Setting | Default | Description |
|---------|---------|-------------|
| `shell_interface` | `"local"` (Docker) | `"local"` = direct shell, `"ssh"` = SSH connection |
| `code_exec_ssh_enabled` | `false` | Enable SSH code execution |
| `code_exec_ssh_addr` | `"localhost"` | SSH host |
| `code_exec_ssh_port` | `22` | SSH port |
| `code_exec_ssh_user` | `"root"` | SSH username |
| `code_exec_ssh_pass` | `""` | SSH password |

### Timeouts

| Setting | Default | Description |
|---------|---------|-------------|
| `code_exec_timeout_first_output` | `30` | Seconds to wait for first output |
| `code_exec_timeout_between_output` | `15` | Seconds between output chunks |
| `code_exec_timeout_max_exec` | `180` | Maximum total execution time (seconds) |
| `code_exec_timeout_dialog` | `5` | Seconds to wait when dialog detected |

---

## RFC (Remote Function Call) Docker Settings

Used when running code inside a Docker container via RFC protocol.

| Setting | Default | Description |
|---------|---------|-------------|
| `rfc_auto_docker` | `true` | Auto-manage Docker RFC container |
| `rfc_url` | `"localhost"` | RFC server address |
| `rfc_password` | `""` | RFC auth password (from `.env`) |
| `rfc_port_http` | `55080` | RFC HTTP port |
| `rfc_port_ssh` | `55022` | RFC SSH port |

---

## Speech (STT/TTS)

| Setting | Default | Description |
|---------|---------|-------------|
| `stt_model_size` | `"base"` | Whisper model: `tiny`, `base`, `small`, `medium`, `large`, `turbo` |
| `stt_language` | `"en"` | STT language code |
| `stt_silence_threshold` | `0.3` | Voice activity detection threshold |
| `stt_silence_duration` | `1000` | ms of silence before stopping recording |
| `stt_waiting_timeout` | `2000` | ms to wait for speech start |
| `tts_kokoro` | `true` | Use Kokoro TTS (local, no API needed) |

---

## MCP (Model Context Protocol)

| Setting | Default | Description |
|---------|---------|-------------|
| `mcp_servers` | `'{"mcpServers": {}}'` | JSON config for external MCP servers |
| `mcp_client_init_timeout` | `10` | Seconds to wait for MCP server init |
| `mcp_client_tool_timeout` | `120` | Seconds to wait for MCP tool response |
| `mcp_server_enabled` | `false` | Expose this agent as an MCP server |
| `mcp_server_token` | *(auto-generated)* | Auth token for MCP server access |

---

## A2A (Agent-to-Agent)

| Setting | Default | Description |
|---------|---------|-------------|
| `a2a_server_enabled` | `false` | Expose this agent as an A2A FastA2A server |

---

## Miscellaneous

| Setting | Default | Description |
|---------|---------|-------------|
| `variables` | `""` | Custom variables (text, injected into prompts) |
| `secrets` | `""` | Custom secrets (from `usr/secrets.env`) |
| `litellm_global_kwargs` | `{}` | Applied to every LiteLLM call |
| `update_check_enabled` | `true` | Check for framework updates on user message |
| `notification_timeout` | `30` | Default notification auto-dismiss (seconds) |

---

## Authentication

Authentication settings come from `.env` file, NOT `usr/settings.json`.

```bash
# .env file
AUTH_LOGIN=admin
AUTH_PASSWORD=yourpassword
ROOT_PASSWORD=rootpassword  # Docker root user password
```

No login/password = UI is accessible without authentication.

---

## Docker Setup

### Standard Docker (non-pentest)

```bash
docker pull agent0ai/agent-zero
docker run -p 50001:80 \
  -v /your/workdir:/a0/usr/workdir \
  -v /your/memory:/a0/usr/memory \
  -e A0_SET_agent_profile=agent0 \
  agent0ai/agent-zero
```

### Pentest Docker (`docker/pentest/`)

The pentest Docker image extends the base image with a full Kali Linux toolchain.

**`docker/pentest/Dockerfile`** — Key additions over base image:

```dockerfile
FROM agent0ai/agent-zero:latest

# Recon tools
RUN apt-get install -y amass subfinder gobuster ffuf feroxbuster

# Web testing
RUN apt-get install -y nikto nuclei seclists

# Post-exploitation & AD
RUN apt-get install -y bloodhound neo4j python3-impacket

# Credential attacks
RUN apt-get install -y hashcat john hydra crackmapexec

# Reporting
RUN pip3 install weasyprint

# Wordlists
RUN apt-get install -y seclists
RUN cd /usr/share/wordlists && gunzip rockyou.txt.gz

# Python deps for pentest tools
RUN pip3 install aiohttp markdown

# Default to hacker profile
ENV A0_SET_agent_profile=hacker
ENV A0_SET_shell_interface=local
```

**`docker/pentest/docker-compose.yml`:**

```yaml
version: "3.8"
services:
  pentest-agent:
    build: .
    ports:
      - "50001:80"
    environment:
      - A0_SET_agent_profile=hacker
      - A0_SET_shell_interface=local
    cap_add:
      - NET_ADMIN   # Required for network interfaces, packet capture
      - NET_RAW     # Required for raw socket access (nmap, etc.)
    volumes:
      - ./data/workdir:/a0/usr/workdir
      - ./data/memory:/a0/usr/memory
      - ./data/settings.json:/a0/usr/settings.json
    network_mode: bridge
```

**Launch:**
```bash
docker compose -f docker/pentest/docker-compose.yml up --build
open http://localhost:50001
```

---

## Secrets Management

**Secrets hierarchy:**

```
1. .env file (root of project)  — API keys, auth passwords
2. usr/secrets.env              — User-defined secrets (injected into agent context)
```

**`usr/secrets.env`** format (key=value):
```
MY_TARGET_VPN_PASS=hunter2
AWS_SECRET_ACCESS_KEY=xxx
```

Secrets from `usr/secrets.env` are loaded into the agent as masked placeholders. The `agent.system.secrets.md` prompt explains to the LLM that it should use the placeholder alias in tool calls; the `_10_unmask_secrets.py` extension substitutes the actual value before the tool executes.

---

## Profile Settings Reference

The `agents/<profile>/settings.json` format:

```json
{
  "agent_profile": "hacker",
  "agent_memory_subdir": "hacker",
  "workdir_path": "usr/workdir",
  "memory_recall_enabled": true,
  "memory_memorize_enabled": true,
  "chat_model_name": "anthropic/claude-opus-4.6"
}
```

Any setting from the main settings dict can appear here. Profile settings are merged AFTER `usr/settings.json` so they win over user settings but lose to environment variables.

---

## Selecting a Profile

Three ways to set the active profile:

```bash
# Environment variable (Docker)
A0_SET_agent_profile=hacker

# Profile's own settings.json (self-selects)
{ "agent_profile": "hacker" }

# UI: Settings → Agent Profile → select from dropdown
```

The currently available profiles: `agent0`, `hacker`, `developer`, `researcher`, `recon`, `exploit-dev`, `reporter`, `default`, `_example`.

See [agent-profiles.md](./agent-profiles.md) for full profile documentation.
