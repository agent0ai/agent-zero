# Agent Zero - Setup and Deployment

## Docker Deployment (Standard)

Agent Zero is distributed as a Docker image: `agent0ai/agent-zero`.

```bash
docker pull agent0ai/agent-zero
docker run -p 50001:80 agent0ai/agent-zero
```

The web UI is then accessible at `http://localhost:50001`. The container exposes port 80 internally; map any host port to it.

## Persistence

All user data lives in `/a0/usr/` inside the container. Without a volume mount, data is lost when the container is removed.

Map `/a0/usr` to a host directory for persistence:
```bash
docker run -p 50001:80 -v /path/on/host:/a0/usr agent0ai/agent-zero
```

Contents of `/a0/usr/`:
- `settings.json` - all configuration including API keys and model settings
- `memory/` - FAISS vector indexes and knowledge import state
- `knowledge/` - user-added knowledge files
- `agents/` - custom agent profiles
- `plugins/` - user plugins
- `projects/` - project workspaces
- `work/` - default working directory for agent file output

## Configuration After Start

On first run, open Settings (gear icon) and configure:
1. **API Keys** - add at least one provider API key under the relevant provider section
2. **Chat Model** - select provider and model name for the primary LLM
3. **Utility Model** - select a cheaper/faster model for internal tasks
4. **Embedding Model** - select embedding provider and model (required for memory and knowledge)

Settings are saved to `usr/settings.json` immediately on change.

## Updating Agent Zero

The recommended update process preserves user data:
1. Keep the old container running
2. Pull the new image: `docker pull agent0ai/agent-zero`
3. Start the new container on a different host port
4. In the old instance: Settings → Backup & Restore → Create Backup
5. In the new instance: Settings → Backup & Restore → Restore from Backup
6. Stop the old container

## Remote Access

### Flare Tunnel (recommended for external access)
Settings → External Services → Flare Tunnel → Create Tunnel

This generates a public HTTPS URL without requiring firewall changes or a static IP. Set a username and password before creating the tunnel to enable authentication.

### Local Network
Access from other devices on the same network using the host machine's IP:
`http://<host-ip>:<mapped-port>`

### Microsoft Dev Tunnels
Supported as an alternative to Flare for users in Microsoft environments. Configure under External Services in Settings.

## Mobile Access

Agent Zero is a Progressive Web App (PWA). On mobile, open the web UI URL in a browser, then add to home screen for an app-like experience. Works with both local network and tunnel URLs.

## Common Troubleshooting

**Agent responds but no memory/knowledge recall:**
- Check that an embedding model is configured (provider + model name)
- Verify the embedding provider API key is set
- Embedding model changes require re-indexing; this happens automatically but takes time on first run

**"Model not found" or API errors:**
- Verify the model name matches the provider's naming convention exactly
- Check that the API key has access to the requested model
- For OpenRouter, model names must include the provider prefix (`anthropic/claude-sonnet-4-5`)

**Container starts but web UI unreachable:**
- Confirm the host port mapping in `docker ps`
- Check that no firewall rule blocks the mapped port
- The container needs a few seconds to initialize on first start

**Knowledge files not being recalled:**
- Supported formats: `.md`, `.txt`, `.pdf`, `.csv`, `.html`, `.json`
- Files must be in `knowledge/` (framework level) or `usr/knowledge/<subdir>/`
- The configured `agent_knowledge_subdir` must match the subdir where files are placed
- Re-indexing is triggered automatically when file checksums change

**Ollama / local model setup:**
- Ollama must be running and accessible from inside the Docker container
- Use `http://host.docker.internal:<port>` as the API URL for Ollama (not `localhost`)
- Pull the model first: `ollama pull <model-name>`

## Development Setup (non-Docker)

```bash
git clone https://github.com/agent0ai/agent-zero
cd agent-zero
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements2.txt
python run_ui.py
```

The dev server runs on `http://localhost:5000` by default. User data is written to `usr/` in the project root.
