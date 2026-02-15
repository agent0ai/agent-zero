# Quick Start Development Setup

Start developing Agent Zero in minutes with these simple steps.

---

## Prerequisites

- **Python 3.12** (required - Python 3.13+ is not supported due to package compatibility)
- **uv** - Fast Python package manager

Install uv:
```powershell
pip install uv
```

---

## Setup Steps

### Step 1: Navigate to Project Directory

```powershell
cd C:\path\to\agent-zero-telegram
```

Navigate to the project folder where you cloned/downloaded Agent Zero.

---

### Step 2: Create Virtual Environment with Python 3.12

```powershell
uv venv --python 3.12
```

Creates a `.venv` folder with Python 3.12. This version is required because some packages (faiss-cpu, onnxruntime) don't support Python 3.13+.

---

### Step 3: Activate Virtual Environment

```powershell
.venv\Scripts\Activate.ps1
```

Activates the virtual environment. You should see `(.venv)` in your terminal prompt.

> **Note:** If you get an execution policy error, run this first:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

---

### Step 4: Install Dependencies

```powershell
$env:UV_HTTP_TIMEOUT="300"; uv pip install -r requirements.txt
```

Installs all Python packages from `requirements.txt`. The timeout is set to 5 minutes to handle large packages.

> **First run:** This may take 3-5 minutes depending on your internet speed.

---

### Step 5: Install Playwright Browsers (Optional)

```powershell
playwright install chromium
```

Installs Chromium browser for web automation features. Skip this if you don't need browser automation.

---

### Step 6: Start the Application

```powershell
python run_ui.py
```

Starts the Agent Zero server. Open your browser to **http://localhost:7080** (or the port configured in `.env`).

---

## Quick Reference

### First-time Setup (All Steps)
```powershell
cd C:\path\to\agent-zero-telegram
uv venv --python 3.12
.venv\Scripts\Activate.ps1
$env:UV_HTTP_TIMEOUT="300"; uv pip install -r requirements.txt
playwright install chromium
python run_ui.py
```

### Daily Development (After First Setup)
```powershell
cd C:\path\to\agent-zero-telegram
.venv\Scripts\Activate.ps1
python run_ui.py
```

---

## Configuration

### Environment Variables (`.env` file)

Create a `.env` file in the project root:

```env
# Web UI Configuration
WEB_UI_PORT=7080
WEB_UI_HOST=localhost

# Hot Reload (auto-restart on code changes)
HOT_RELOAD=true

# API Keys (configure in web UI Settings or add here)
# OPENROUTER_API_KEY=sk-or-v1-your-key-here
# API_KEY_OPENAI=sk-your-openai-key-here
```

---

## Development Features

### Hot Reload

When `HOT_RELOAD=true` in `.env`, the server automatically restarts when you change Python files.

| File Type | Behavior |
|-----------|----------|
| Python (`.py`) | Auto-restart server |
| HTML/JS/CSS | Refresh browser |

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `uv is not installed` | Run `pip install uv` |
| `No module named 'litellm'` | Dependencies incomplete - re-run Step 4 |
| `faiss-cpu has no wheels` | Use Python 3.12, not 3.13+ |
| `Port already in use` | Change `WEB_UI_PORT` in `.env` |
| Execution policy error | Run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` |

---

## Next Steps

1. Open **http://localhost:7080** in your browser
2. Configure your API keys in **Settings > API Keys**
3. Start chatting with Agent Zero!

---

## Coolify Deployment (Production)

Deploy your local source code to Coolify using the official Kali Linux base image.

### How It Works

| Component | Description |
|-----------|-------------|
| Base Image | `agent0ai/agent-zero-base:latest` (Kali Linux) |
| Source Code | Your local code (copied instead of cloned from GitHub) |
| Port | `80` (mapped to external port) |

### Step 1: Push Code to Git Repository

Push your code to a Git repository (GitHub, GitLab, Gitea, etc.) that Coolify can access.

### Step 2: Create Coolify Resource

In Coolify dashboard:

1. **New Resource** → **Docker Compose** (or **Service** → **Dockerfile**)
2. Connect your Git repository
3. Set the following:

| Setting | Value |
|---------|-------|
| Dockerfile | `Dockerfile.coolify` |
| Or Docker Compose | `docker-compose.coolify.yml` |
| Port | `80` |

### Step 3: Configure Environment Variables

In Coolify's environment variables section, add:

```env
BRANCH=local
WEB_UI_PORT=80
WEB_UI_HOST=0.0.0.0

# Add your API keys
OPENROUTER_API_KEY=sk-or-v1-your-key-here
API_KEY_OPENAI=sk-your-openai-key-here
```

### Step 4: Deploy

Click **Deploy** in Coolify. Your source code will be built using Kali Linux and deployed.

### Files for Coolify

| File | Purpose |
|------|---------|
| `Dockerfile.coolify` | Uses Kali base image + your source code |
| `docker-compose.coolify.yml` | Docker Compose with volume persistence |
| `.dockerignore` | Excludes unnecessary files from build |
| `docker/run/fs/*` | Build scripts (required, included in build) |

### What Gets Built

1. **Base**: Kali Linux with all tools pre-installed
2. **Your Code**: Copied to `/git/agent-zero` (instead of cloning from GitHub)
3. **Dependencies**: Installed from your `requirements.txt`
4. **Services**: SearXNG, SSH, MCP/A2A support

---

## Additional Resources

- [Full Documentation](./README.md)
- [Development Guide](./docs/setup/dev-setup.md)
- [Usage Guide](./docs/guides/usage.md)
