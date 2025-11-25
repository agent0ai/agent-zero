# Docker Network & Qdrant MCP Server Improvements

## Overview

This document describes the improvements made to consolidate the Docker network configuration and add a dedicated Qdrant MCP server for collection administration and optimization.

## Changes Summary

### 1. Consolidated Docker Compose (`docker-compose.yml`)

**Key Improvements:**
- **DNS-based service discovery** - Removed static IP assignments (172.30.0.x) in favor of Docker's built-in DNS
- **Unified configuration** - Single docker-compose.yml replaces multiple fragmented configs
- **Proper healthchecks** - All services now have working health checks
- **New Qdrant MCP Server** - Dedicated container for Qdrant administration

**Services:**
| Service | Port | Description |
|---------|------|-------------|
| agent-zero-unity | 50001 | Main AI assistant |
| qdrant-unity | 6333, 6334 | Vector database (HTTP, gRPC) |
| qdrant-mcp-server | 9060 | **NEW** Qdrant admin MCP server |
| unity-mcp-server | 9050, 9051 | Unity Editor integration |
| redis-cache | 6379 | Session/embedding cache |

### 2. Qdrant MCP Server (`qdrant-mcp-server/`)

A new FastMCP-based server providing 15 administration tools:

**Collection Management:**
- `qdrant_list_collections` - List all collections with stats
- `qdrant_create_collection` - Create with custom vector config
- `qdrant_delete_collection` - Delete with confirmation
- `qdrant_get_collection_info` - Detailed collection info
- `qdrant_update_collection` - Update HNSW/optimizer settings

**Point Operations:**
- `qdrant_count_points` - Count with optional filtering
- `qdrant_get_points` - Retrieve by IDs
- `qdrant_scroll_points` - Paginated retrieval
- `qdrant_upsert_points` - Insert/update points
- `qdrant_delete_points` - Delete by IDs or filter

**Search Operations:**
- `qdrant_search_vectors` - Similarity search
- `qdrant_search_batch` - Multi-query batch search
- `qdrant_recommend_points` - "More like this" recommendations

**Admin Operations:**
- `qdrant_optimize_collection` - Trigger optimization
- `qdrant_create_snapshot` - Create backups
- `qdrant_list_snapshots` - List available snapshots
- `qdrant_get_cluster_info` - Instance overview
- `qdrant_health_check` - Connectivity check

### 3. Scripts

| Script | Description |
|--------|-------------|
| `scripts/docker-start.sh` | Start all services with health checks |
| `scripts/setup-qdrant-kb.sh` | Initialize Qdrant knowledge base |
| `scripts/healthcheck.py` | Check all service health |

### 4. Configuration Templates

- `.env.example` - Environment variables template
- `claudedocs/config_templates/mcp_servers_example.json` - MCP server config example

## Quick Start

### 1. Setup Environment

```bash
# Copy environment template
cp .env.example .env

# Edit with your API keys
nano .env
```

### 2. Start Services

```bash
# Start all services
docker compose up -d

# Or with rebuild
docker compose up -d --build

# Check health
python scripts/healthcheck.py
```

### 3. Initialize Qdrant Knowledge Base

```bash
# From inside agent-zero-unity container
docker exec -it agent-zero-unity bash
./scripts/setup-qdrant-kb.sh
```

### 4. Configure MCP Server in Agent Zero

Add to your Agent Zero settings (via UI or `tmp/settings.json`):

```json
{
  "mcp_servers": "[{\"name\": \"qdrant-admin\", \"type\": \"sse\", \"url\": \"http://qdrant-mcp-server:8080/sse\", \"disabled\": false}]"
}
```

## Architecture

```
                                    ┌─────────────────┐
                                    │   Claude Code   │
                                    │  (Your Machine) │
                                    └────────┬────────┘
                                             │ MCP
                                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Docker: unity-network                         │
│                                                                  │
│  ┌──────────────────┐    ┌──────────────────┐                   │
│  │  agent-zero-unity│    │  qdrant-mcp-server│◄──── NEW         │
│  │     :50001       │    │      :9060        │                   │
│  └────────┬─────────┘    └────────┬─────────┘                   │
│           │                       │                              │
│           │      ┌────────────────┴────────────────┐            │
│           │      │                                  │            │
│           ▼      ▼                                  ▼            │
│  ┌──────────────────┐    ┌──────────────────┐    ┌───────────┐  │
│  │   qdrant-unity   │    │  unity-mcp-server│    │redis-cache│  │
│  │   :6333, :6334   │    │   :9050, :9051   │    │   :6379   │  │
│  └──────────────────┘    └──────────────────┘    └───────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

### Memory Operations (Agent Zero → Qdrant)
```
Agent Zero → Memory Module → QdrantStore → Qdrant HTTP API
```

### Admin Operations (Claude Code → Qdrant MCP)
```
Claude Code → MCP Protocol → qdrant-mcp-server → Qdrant HTTP API
                                   │
                                   └── Full admin capabilities:
                                       - Collection management
                                       - Optimization controls
                                       - Backup/snapshot
                                       - Statistics/metrics
```

## Files Changed/Added

### New Files
```
docker-compose.yml                           # Consolidated config
qdrant-mcp-server/
├── Dockerfile
├── requirements.txt
├── config.py
├── server.py
└── tools/
    ├── __init__.py
    ├── collections.py
    ├── points.py
    ├── search.py
    └── admin.py
scripts/
├── docker-start.sh
├── setup-qdrant-kb.sh
└── healthcheck.py
.env.example
claudedocs/config_templates/mcp_servers_example.json
```

### Preserved Files
- `docker-compose-unity-enhanced.yml` - Original config (for reference)
- `python/helpers/mcp_qdrant_server.py` - Existing memory MCP tools
- `python/helpers/qdrant_client.py` - Existing Qdrant wrapper

## Troubleshooting

### Services not starting
```bash
# Check logs
docker compose logs -f qdrant-mcp-server

# Check health
python scripts/healthcheck.py --json
```

### Cannot connect to Qdrant
```bash
# Verify Qdrant is running
curl http://localhost:6333/

# Check from inside container
docker exec agent-zero-unity curl http://qdrant-unity:6333/
```

### MCP tools not appearing
1. Check MCP server is running: `curl http://localhost:9060/health`
2. Verify settings in Agent Zero UI
3. Check MCP server logs: `docker compose logs qdrant-mcp-server`

## Next Steps

1. **Test the integration** - Use `qdrant_admin.qdrant_health_check` tool
2. **Initialize knowledge base** - Run `setup-qdrant-kb.sh`
3. **Ingest Unity documentation** - Run ingestion scripts
4. **Monitor performance** - Use `qdrant_admin.qdrant_get_collection_info`
