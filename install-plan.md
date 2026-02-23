# Agent Zero Install Script - Improvement Plan

## Overview

Upgrade the installation script from a linear POSIX-only installer into a cross-platform interactive CLI tool that handles both installation and container management. Two scripts: `install.sh` (POSIX) and `install.ps1` (Windows PowerShell).

### User-facing one-liners

```
# macOS / Linux
curl -fsSL https://agent-zero.ai/install.sh | sh

# Windows (PowerShell)
irm https://agent-zero.ai/install.ps1 | iex
```

Hosting: Scripts live in the GitHub repo. `agent-zero.ai` redirects/proxies to the raw GitHub URLs.

---

## Current State (install.sh v1)

The existing script is a straightforward linear flow:
1. Detect/install Docker (via `get.docker.com`)
2. Prompt for data directory, port, and auth credentials
3. Generate a `docker-compose.yml` at `~/.agentzero/`
4. Pull `agent0ai/agent-zero` (always `latest`) and start with `docker compose up -d`

### What it lacks
- No Windows support
- No version selection (always pulls `latest`)
- No management of existing containers (start/stop/restart/delete/open)
- No detection of existing Agent Zero containers
- No interactive menu (linear flow only)

---

## Target Architecture

### Two scripts, feature-parity

| | `install.sh` | `install.ps1` |
|---|---|---|
| Shell | POSIX `sh` (no bash-isms) | PowerShell 5.1+ (ships with Win10/11) |
| Docker install | Auto via `get.docker.com` (Linux) / guide for macOS | Guide to Docker Desktop download page |
| Container runtime | `docker compose` (plugin) or `docker-compose` (standalone) | `docker compose` via Docker Desktop |
| Menu | Numbered interactive menu | Numbered interactive menu |
| Version fetch | Docker Hub Registry API | Docker Hub Registry API |

### Shared behavior

Both scripts show the same interactive menu, use the same Docker Hub API for version listing, produce compatible `docker-compose.yml` files, and detect containers by image name `agent0ai/agent-zero`.

---

## Interactive Menu Flow

On launch, the script checks for Docker, then shows:

```
========== Agent Zero ==========

  1) Create new instance
  2) Manage existing instances
  3) Exit

Select an option [1-3]:
```

### 1) Create new instance

```
Step 1 - Select version:
  1) latest
  2) testing
  3) development
  4) v0.9.8
  5) v0.9.7
  ...
  13) v0.9.0
  14) Enter custom tag

Step 2 - Container name:
  Name [agent-zero]:

Step 3 - Data directory:
  Where to store user data? [~/.agentzero/<name>/usr]:

Step 4 - Web UI port:
  Port [5080]:

Step 5 - Authentication:
  Username (empty = no auth):
  Password [12345678]:

--> Pulling image...
--> Starting container...
--> Done! Opening http://localhost:5080 in browser...
```

### 2) Manage existing instances

Detects all running/stopped containers using `agent0ai/agent-zero*` image:

```
  Existing Agent Zero instances:
  ─────────────────────────────────────────────────
  #  Name           Version   Port    Status
  1  agent-zero     v0.9.8    5080    running
  2  agent-zero-2   v0.9.7    5081    stopped
  ─────────────────────────────────────────────────

  Select instance [1-2]: 1

  Actions for "agent-zero":
  1) Open in browser
  2) Start
  3) Stop
  4) Restart
  5) Delete (remove container + optional data)
  6) View logs
  7) Update (pull latest image + restart)
  8) Back

  Select action [1-8]:
```

If no existing containers are found, the menu says so and offers to create a new one.

---

## Detailed Task Breakdown

### Task 1: Refactor install.sh into interactive menu structure

**What changes from current script:**
- Wrap the existing linear install flow into a `create_instance()` function
- Add a main menu loop with numbered options
- Add a `manage_instances()` function
- Keep the same ASCII art banner and color scheme

**Key functions to implement:**
- `main_menu()` — top-level menu loop
- `check_docker()` — existing Docker detection (keep mostly as-is)
- `create_instance()` — refactored from current steps 2-5, plus version selection
- `list_instances()` — query Docker for agent-zero containers
- `manage_instance()` — start/stop/restart/delete/open/logs/update actions
- `fetch_versions()` — call Docker Hub API for available tags
- `open_browser()` — detect OS and use `xdg-open` / `open` / `wslview`

**Container detection approach:**
```sh
docker ps -a --filter "ancestor=agent0ai/agent-zero" \
  --format '{{.Names}}\t{{.Image}}\t{{.Ports}}\t{{.Status}}'
```

This catches all containers regardless of tag, including stopped ones.

### Task 2: Add version selection via Docker Hub API

**API endpoint:**
```
GET https://registry.hub.docker.com/v2/repositories/agent0ai/agent-zero/tags/?page_size=15&ordering=last_updated
```

**Response parsing:**
- Use `curl` + lightweight JSON parsing (grep/sed or `python3 -c` if available)
- Extract tag names, filter out architecture-specific tags
- Present special tags first (`latest`, `testing`, `development`), then version tags sorted by semver

**Fallback:** If the API call fails (no internet, API down), offer only manual tag entry and `latest` as default.

**PowerShell equivalent:**
```powershell
$tags = Invoke-RestMethod "https://registry.hub.docker.com/v2/repositories/agent0ai/agent-zero/tags/?page_size=15&ordering=last_updated"
$tags.results | Select-Object -ExpandProperty name
```

### Task 3: Implement container management actions

Each action maps to a simple Docker command:

| Action | Command |
|--------|---------|
| Open in browser | `xdg-open` / `open` / `Start-Process` on `http://localhost:<port>` |
| Start | `docker start <name>` |
| Stop | `docker stop <name>` |
| Restart | `docker restart <name>` |
| Delete | `docker rm -f <name>` (ask to also delete data dir) |
| View logs | `docker logs -f --tail 50 <name>` |
| Update | `docker pull <image>:<tag> && docker stop <name> && docker rm <name> && docker run ...` (recreate with same config) |

**Port detection** (for "open in browser"):
```sh
docker port <name> 80 | head -1  # returns e.g. 0.0.0.0:5080
```

**Update strategy:** Store the original `docker run` parameters. On update, pull the new image, stop + remove the old container, and recreate with the same config. The compose file at `~/.agentzero/<name>/docker-compose.yml` serves as the source of truth.

### Task 4: Container naming with smart defaults

- Default name: `agent-zero`
- If `agent-zero` already exists, suggest `agent-zero-2`, then `agent-zero-3`, etc.
- User can type a custom name
- Each instance gets its own directory: `~/.agentzero/<name>/` containing its `docker-compose.yml` and default data dir at `~/.agentzero/<name>/usr/`

### Task 5: Create install.ps1 (Windows PowerShell)

**Feature parity with install.sh**, adapted for Windows:

- **Docker detection:** Check if `docker` command exists. If not, print a message with the Docker Desktop download URL (`https://www.docker.com/products/docker-desktop/`) and open it in the default browser via `Start-Process`. Exit with instructions to re-run after installing.
- **Menu system:** Same numbered menus, using `Read-Host` for input.
- **Colors:** Use `Write-Host -ForegroundColor` for colored output.
- **Version fetching:** `Invoke-RestMethod` (built into PowerShell, no curl needed).
- **Open browser:** `Start-Process "http://localhost:$port"`
- **Data directory:** Default to `$env:USERPROFILE\.agentzero\<name>\usr`
- **Compose file generation:** Same YAML output, written with `Set-Content`.

**Key differences from POSIX script:**
- No `get.docker.com` auto-install (Docker Desktop is a GUI installer on Windows)
- Path separators handled natively by PowerShell
- No need for `sudo` / user group management

### Task 6: Script hosting setup

**GitHub side:**
- Both `install.sh` and `install.ps1` live in the repo root

**Web side (agent-zero.ai):**
- `https://agent-zero.ai/install.sh` → redirects or proxies to `https://raw.githubusercontent.com/agent0ai/agent-zero/main/install.sh`
- `https://agent-zero.ai/install.ps1` → redirects or proxies to `https://raw.githubusercontent.com/agent0ai/agent-zero/main/install.ps1`
- Simple redirect (HTTP 302) or a static proxy config — either works for `curl | sh` and `irm | iex`

---

## Implementation Order

| # | Task | Depends on | Effort |
|---|------|------------|--------|
| 1 | Refactor `install.sh` — menu structure, function extraction | — | Medium |
| 2 | Add version selection (Docker Hub API + JSON parsing) | 1 | Medium |
| 3 | Implement container management actions | 1 | Medium |
| 4 | Container naming with smart defaults | 1 | Small |
| 5 | Create `install.ps1` with feature parity | 1-4 (use as spec) | Large |
| 6 | Script hosting setup on agent-zero.ai | 5 | Small |

Tasks 1-4 can be developed incrementally on `install.sh`. Task 5 follows once the POSIX script behavior is finalized (so the PS1 script mirrors it). Task 6 is a deployment/infra task.

---

## Technical Notes

### JSON parsing in POSIX sh

Docker Hub returns JSON. Options for parsing without `jq`:
1. **`python3 -c`** — Likely available since Agent Zero is Python-based. Most reliable.
2. **`grep` / `sed`** — Fragile but zero-dependency. Workable for the simple tag-list structure.
3. **`jq`** — Best tool for the job but adds a dependency.

Recommended: Try `python3` first, fall back to `grep/sed` parsing.

```sh
fetch_versions() {
    url="https://registry.hub.docker.com/v2/repositories/agent0ai/agent-zero/tags/?page_size=15&ordering=last_updated"
    response=$(curl -fsSL "$url" 2>/dev/null) || { echo "latest"; return; }

    if command -v python3 > /dev/null 2>&1; then
        echo "$response" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for t in data.get('results', []):
    print(t['name'])
"
    else
        # Fallback: grep for tag names
        echo "$response" | grep -o '"name":"[^"]*"' | sed 's/"name":"//;s/"//'
    fi
}
```

### Compose file per instance

Each instance gets its own directory and compose file:
```
~/.agentzero/
  agent-zero/
    docker-compose.yml
    usr/                   # default data dir
  agent-zero-2/
    docker-compose.yml
    usr/
```

This replaces the current single `~/.agentzero/docker-compose.yml` approach and enables managing multiple instances independently.

**Migration:** If the script detects the old single-instance layout (`~/.agentzero/docker-compose.yml` without subdirectories), it should migrate it to `~/.agentzero/agent-zero/docker-compose.yml` automatically.

### Docker Compose vs docker run

The current script uses `docker compose`. We should keep this approach because:
- Compose files serve as persistent configuration (source of truth for updates)
- `docker compose up -d` is idempotent
- Easy to add future services (e.g., Ollama sidecar)

Each instance uses `docker compose -f <path>/docker-compose.yml` for its operations.

### Browser opening

```sh
open_browser() {
    url="$1"
    case "$(uname -s)" in
        Darwin)  open "$url" ;;
        Linux)   xdg-open "$url" 2>/dev/null || echo "Open: $url" ;;
        *)       echo "Open: $url" ;;
    esac
}
```

PowerShell: `Start-Process $url`

---

## Out of Scope (handled elsewhere)

- **Onboarding flow** (provider selection, API keys, model config) — handled by the A0 onboarding plugin inside the running container
- **CI/CD pipeline** for building/pushing Docker images — separate concern
- **Auto-update of the install script itself** — not needed for v2
