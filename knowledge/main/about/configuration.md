# Agent Zero - Configuration Reference

## LLM Roles

Agent Zero uses three configurable LLM roles:

| Role | Purpose |
|------|---------|
| `chat_llm` | Primary model for all agent reasoning, tool use, and the Browser Agent |
| `utility_llm` | Secondary model for internal framework tasks: memory summarization, query generation, history compression, memory recall filtering |
| `embedding_llm` | Produces vector embeddings for memory and knowledge indexing |

The utility model handles high-volume, lower-stakes operations and can be a cheaper/faster model than the chat model. The Browser Agent uses the effective chat model resolved by `_model_config`, including per-chat overrides and the chat model vision flag. Changing the embedding model invalidates the existing vector index - the entire knowledge base is re-indexed automatically.

## Model Providers

Providers are defined in `conf/model_providers.yaml`. All chat and embedding providers go through LiteLLM, which normalizes the API interface. Supported chat providers (as of v0.9.8):

- Agent Zero API (a0_venice) - hosted service with no API key required for basic use
- Anthropic, OpenAI, OpenRouter, Google (Gemini), Groq, Mistral AI
- DeepSeek, xAI, Moonshot AI, Sambanova, CometAPI, Z.AI, Inception AI
- Venice.ai, AWS Bedrock, Azure OpenAI
- GitHub Copilot, HuggingFace
- Ollama, LM Studio (local models)
- Other OpenAI-compatible endpoints (custom `api_base`)

Embedding providers: OpenAI, Azure, Ollama, LM Studio, HuggingFace, Google, Mistral, OpenRouter (via OpenAI-compat), AWS Bedrock.

### Model Naming Convention

| Provider | Format |
|----------|--------|
| OpenAI | model name only (`gpt-4.1`, `o4-mini`) |
| Anthropic | model name only (`claude-sonnet-4-5`) |
| OpenRouter | `provider/model` (`anthropic/claude-sonnet-4-5`) |
| Ollama | model name only (`llama3.2`, `qwen2.5`) |
| Google | model name only (`gemini-2.0-flash`) |

## Agent Profiles

Profiles are in `agents/<profile>/`. Each profile can override any prompt fragment from the base `prompts/` directory. Built-in profiles:

| Profile | Description |
|---------|-------------|
| `default` | Base template for creating new profiles |
| `agent0` | Top-level general assistant; human as superior; delegates to specialized subordinates |
| `developer` | "Master Developer" - software architecture and full-stack implementation focus |
| `researcher` | "Deep Research" - research, analysis, and synthesis across academic and corporate domains |
| `hacker` | Red/blue team; penetration testing; Kali tools focus |
| `_example` | Minimal example for building custom profiles |

Custom profiles go in `usr/agents/<profile>/` to survive framework updates.

## Plugin System

Plugins are discovered from `plugins/` (framework plugins) and `usr/plugins/` (user plugins). Each plugin requires a `plugin.yaml` with at minimum: `name`, `description`, `version`.

### Activation

- **Global activation**: enabled/disabled for all contexts via the Plugins settings panel
- **Scoped activation**: enabled/disabled per project or per agent profile via the plugin Switch modal
- Activation state stored as `.toggle-1` (ON) and `.toggle-0` (OFF) files in the plugin's config dir

### Built-in Framework Plugins

| Plugin | Purpose |
|--------|---------|
| `_memory` | Memory and knowledge pipeline, recall, consolidation |
| `_code_execution` | Terminal and code execution tool |
| `_text_editor` | Structured file read/write/patch tool |

## Environment Variable Configuration

Any setting can be set via environment variable using the `A0_SET_` prefix. This is the primary mechanism for automated deployment and container configuration.

Format: `A0_SET_<setting_name>=<value>`

Examples:
```
A0_SET_chat_model_provider=anthropic
A0_SET_chat_model_name=claude-sonnet-4-5
A0_SET_utility_model_provider=openai
A0_SET_utility_model_name=gpt-4o-mini
A0_SET_embedding_model_provider=openai
A0_SET_embedding_model_name=text-embedding-3-small
```

These can be set in the `.env` file at the project root or passed as Docker `-e` flags during container creation.

## Key Behavioral Settings

| Setting | Effect |
|---------|--------|
| `agent_knowledge_subdir` | Which knowledge subdir to load (default: `custom`, resolved to `usr/knowledge/`) |
| `memory_recall_interval` | How many loop iterations between automatic memory recalls |
| `memory_results` | Number of memory chunks returned per recall query |
| `memory_threshold` | Similarity threshold for memory recall (0-1); lower = more results, potentially less relevant |
| `auth_login` / `auth_password` | Web UI authentication credentials |
| `agent_temperature` | LLM temperature for the chat model |

Settings are stored in `usr/settings.json` and managed through the Settings page in the web UI. The settings page also provides: API key management (multiple keys per provider with round-robin), backup/restore, external services (tunnels, MCP, A2A), and memory management.
