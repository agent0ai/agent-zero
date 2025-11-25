# Docker Compose Unity Enhanced - Fixed Issues

## Issues Found and Resolved

### 1. ❌ Mount Error - Config Files
**Problem**: Docker couldn't mount config files:
```
error mounting "/run/desktop/mnt/host/d/GithubRepos/agent-zero/conf/qdrant_config.yaml"
```

**Solution**: Commented out optional config file mounts (lines 116, 174). Qdrant and Unity MCP will use their default configurations.

### 2. ❌ Deprecated Model Names
**Problem**: Using `gemini-3-pro-preview` which doesn't exist.

**Solution**: Updated to current Gemini 2.5 models:
- Chat: `gemini-2.5-pro`
- Utility: `gemini-2.5-flash`

### 3. ❌ Case Sensitivity
**Problem**: Provider names had inconsistent casing (`Google` vs `google`).

**Solution**: Standardized to lowercase `google`.

## Current Configuration

### Agent Zero
- Image: `agent-zero-unity:latest`
- Memory: 12GB limit, 4GB reserved
- CPUs: 6 cores limit, 2 cores reserved
- Profile: `unity_developer`
- Network: `172.30.0.10`

### Qdrant
- Image: `qdrant/qdrant:v1.12.1`
- Memory: 4GB limit, 1GB reserved
- Optimized for Unity knowledge with HNSW indexing
- Network: `172.30.0.20`

### Unity MCP Server
- Image: `ivanmurzakdev/unity-mcp-server:latest`
- Port: 9050 (API), 9051 (WebSocket)
- Network: `172.30.0.30`

### Redis Cache
- Image: `redis:7-alpine`
- Memory: 512MB limit
- Used for session and query caching
- Network: `172.30.0.40`

## How to Use

### Start the Stack
```powershell
cd D:\GithubRepos\agent-zero
docker-compose -f docker-compose-unity-enhanced.yml up -d
```

### Check Status
```powershell
docker-compose -f docker-compose-unity-enhanced.yml ps
```

### View Logs
```powershell
docker-compose -f docker-compose-unity-enhanced.yml logs -f agent-zero-unity
```

### Stop the Stack
```powershell
docker-compose -f docker-compose-unity-enhanced.yml down
```

## Environment Variables

Create a `.env` file with:
```env
# Required
GEMINI_API_KEY=your-google-ai-studio-api-key

# Optional (defaults are set)
UNITY_PROJECT_NAME=UnityMLcreator
UNITY_EDITOR_VERSION=6000.2.10f1
CHAT_MODEL_PROVIDER=google
CHAT_MODEL_NAME=gemini-2.5-pro
UTIL_MODEL_PROVIDER=google
UTIL_MODEL_NAME=gemini-2.5-flash
```

## Volumes

All volumes use the `driver: local` setup:
- `agent-zero-data` → Bind mount to `./data`
- `unity-memory-cache` → For Agent Zero memory
- `qdrant-data` → Qdrant vector database
- `qdrant-snapshots` → Qdrant backups
- `redis-data` → Redis persistence

## Network Architecture

All services run on the `unity-net` bridge network (172.30.0.0/16):
- Gateway: 172.30.0.1
- Agent Zero: 172.30.0.10
- Qdrant: 172.30.0.20
- Unity MCP: 172.30.0.30
- Redis: 172.30.0.40

---

**Status**: ✅ Ready to deploy  
**Date**: 2025-11-25
