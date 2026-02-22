# Phase 6 — Docker and Infrastructure

## Status: COMPLETE

## What Was Done

Created `docker/pentest/Dockerfile` and `docker/pentest/docker-compose.yml`. These extend the standard Agent Zero image rather than rebuilding from scratch, minimizing build time.

---

## Files Created

### `docker/pentest/Dockerfile`

Extends `agent0ai/agent-zero:latest` (the full agent-zero runtime image).

**Packages added via apt-get:**

| Category | Tools |
|----------|-------|
| Recon & OSINT | amass, subfinder |
| Web testing | gobuster, ffuf, feroxbuster, nikto, nuclei |
| Exploitation | seclists, python3-impacket |
| Post-exploit & AD | bloodhound, neo4j |
| Reporting | weasyprint, python3-weasyprint |
| Additional | dnsrecon, whatweb, wafw00f, sslscan, enum4linux-ng, crackmapexec, evil-winrm, proxychains4 |

**Python packages added to venv:**
- `aiohttp` — required for `cve_lookup.py` NVD API async HTTP calls
- `markdown` — required for `report_generator.py` HTML conversion
- `nvdlib` — alternative NVD API client

**Other setup:**
- Extracts `rockyou.txt.gz` if not already extracted
- Creates `/a0/usr/workdir/engagements` workspace directory
- Sets `A0_SET_agent_profile=hacker` as default environment variable

---

### `docker/pentest/docker-compose.yml`

| Setting | Value | Reason |
|---------|-------|--------|
| Port | 50001:80 | Separate from the default 50080 to avoid conflict with stock agent-zero |
| `A0_SET_agent_profile` | hacker | Activates hacker profile on startup |
| `A0_SET_shell_interface` | local | Use the container's shell directly (not SSH) |
| `network_mode` | bridge | Isolated by default; swap to `host` for LAN scanning |
| `NET_ADMIN`, `NET_RAW` | cap_add | Required for nmap OS detection, aircrack-ng, raw sockets |
| Volumes | `usr/workdir`, `usr/memory`, `usr/settings.json` | Engagement data and memory persist between container restarts |

**Network modes:**
- `bridge` (default): container is isolated; for scanning external or VPN targets
- `host` (comment in to enable): container shares host network stack; needed for scanning local LAN hosts that don't route through the Docker bridge

---

## Build and Run

```bash
# From repo root
docker compose -f docker/pentest/docker-compose.yml up --build

# Access web UI
open http://localhost:50001

# Rebuild only (no cache)
docker compose -f docker/pentest/docker-compose.yml build --no-cache

# Run with host networking for LAN scanning
# Edit docker-compose.yml: change network_mode to "host", remove ports mapping
docker compose -f docker/pentest/docker-compose.yml up
```

## Environment Variable Configuration

API keys can be passed via environment or a `.env` file in `docker/pentest/`:

```bash
# docker/pentest/.env
ANTHROPIC_API_KEY=sk-ant-xxx
OPENAI_API_KEY=sk-xxx
```

Or set directly in the UI after first launch via Settings.
