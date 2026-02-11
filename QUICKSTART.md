# Quickstart

## Prerequisites

- [mise](https://mise.jdx.dev) (installs Python 3.12, uv, ruff, biome, git-cliff, hk automatically)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (for code execution sandbox and deployment)
- Git

## 1. Clone and Setup

```bash
git clone https://github.com/jrmatherly/apollos-ai.git
cd apollos-ai
mise install          # Install all tools (Python 3.12, uv, ruff, biome, etc.)
mise run setup        # Install deps, Playwright browser, git hooks
```

This runs `uv sync --group dev`, installs Chromium for browser automation, and configures hk git hooks.

## 2. Configure

Copy the example env file and add your API keys:

```bash
cp usr/.env.example usr/.env
# Edit usr/.env with your API keys and model preferences
```

Or skip this and configure via the web UI after starting (Settings > API Keys).

See `docs/reference/environment-variables.md` for the complete variable catalog.

### Branding

To customize the project name displayed in the UI:

```bash
# In usr/.env
BRAND_NAME=My Custom AI
```

See [Environment Variables Reference](docs/reference/environment-variables.md#branding-configuration) for all branding options.

Supported providers: Anthropic, OpenAI, OpenRouter, Ollama (local), and [many more via LiteLLM](https://docs.litellm.ai/docs/providers).

## 3. Run Locally

```bash
mise run r            # Start UI server
```

Open `http://localhost:5000` (or the port shown in terminal output). Configure your API key in Settings if you didn't use `.env`.

**Code execution requires Docker.** The agent executes code inside a container. Start a Docker instance alongside your local dev server:

```bash
docker pull ghcr.io/jrmatherly/apollos-ai
docker run -p 8880:80 -p 8822:22 ghcr.io/jrmatherly/apollos-ai
```

Then in the web UI: Settings > Development > set RFC password (same on both instances), SSH port `8822`, HTTP port `8880`.

## 4. Run with Docker Only

For a self-contained deployment without a local dev environment:

```bash
# Pull and run
docker run -p 50080:80 -v ./apollos-ai-data:/a0/usr ghcr.io/jrmatherly/apollos-ai

# Or use Docker Compose
cd docker/run
docker-compose up -d
```

Open `http://localhost:50080`. The `-v` flag persists data across container restarts.

**Do not** mount the entire `/a0` directory — only `/a0/usr` for user data.

## 5. Build Local Docker Image

```bash
mise run docker:build    # Build from DockerfileLocal
mise run docker:run      # Run on port 50080
```

## 6. Development Workflow

```bash
mise run lint            # Lint Python (Ruff) + CSS (Biome)
mise run format:check    # Check formatting without modifying
mise run t               # Run tests
mise run ci              # All checks: lint + format + test
```

Single test file:

```bash
uv run pytest tests/test_websocket_manager.py -v
```

Git hooks (hk) run automatically on commit: Ruff, Biome, security checks, conventional commit format.

## 7. Dependency Management

```bash
mise run deps:add <package>     # Add + regenerate requirements.txt
mise run deps:add-dev <package> # Add to dev group
mise run deps:export            # Regenerate requirements.txt from pyproject.toml
```

Never edit `requirements.txt` manually — it's auto-generated for Docker compatibility.

## 8. Deploy to VPS

Server requirements: 2+ GB RAM, 20+ GB storage, Docker Engine 24.0+.

```bash
# On the server
docker pull ghcr.io/jrmatherly/apollos-ai
docker run -d --restart unless-stopped \
  -p 50080:80 \
  -v /opt/apollos-ai/usr:/a0/usr \
  ghcr.io/jrmatherly/apollos-ai
```

Set up a reverse proxy (Apache/Nginx) with SSL for production. Enable WebSocket proxying for Socket.IO. Set authentication in Settings > Authentication before exposing to the internet.

See `docs/setup/vps-deployment.md` for full Apache/SSL/domain configuration.

## 9. Release

Releases are automated via GitHub Actions on tag push:

```bash
git tag v0.1.0
git push origin v0.1.0
```

This generates a changelog (git-cliff from conventional commits) and creates a GitHub release.

## Key Paths

| Path | Purpose |
|------|---------|
| `run_ui.py` | Main entry point |
| `agent.py` | Core agent loop |
| `python/tools/` | Agent tools (auto-discovered) |
| `python/api/` | REST endpoints (auto-discovered) |
| `python/extensions/` | Lifecycle hooks (auto-discovered) |
| `python/helpers/` | Utility modules |
| `prompts/` | System prompt templates |
| `webui/` | Frontend (Alpine.js) |
| `usr/.env` | Environment/API config (gitignored, see `usr/.env.example`) |
| `pyproject.toml` | Python dependencies (source of truth) |
| `mise.toml` | Task runner + tool definitions |

## Further Reading

- `docs/setup/installation.md` — Full installation guide with OS-specific instructions
- `docs/setup/dev-setup.md` — IDE setup with debugger, RFC/Docker hybrid workflow
- `docs/setup/vps-deployment.md` — Production deployment with reverse proxy and SSL
- `docs/developer/architecture.md` — Architecture overview
- `docs/developer/extensions.md` — Extension system and lifecycle hooks
- `docs/guides/mcp-setup.md` — MCP server configuration
- `docs/guides/a2a-setup.md` — Agent-to-Agent protocol setup
