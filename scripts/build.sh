#!/bin/bash
# Build script with GCP model management
# Integrates model versioning into the build process

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPT_DIR="${PROJECT_ROOT}/scripts"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[BUILD]${NC} $1"
}

log_step() {
    echo -e "${YELLOW}[STEP]${NC} $1"
}

# Configuration
BUILD_ENV="${BUILD_ENV:-production}"
SKIP_MODEL_DOWNLOAD="${SKIP_MODEL_DOWNLOAD:-false}"
MODEL_VERSION="${MODEL_VERSION:-latest}"

log_info "Starting Agent Jumbo build process"
log_info "Environment: ${BUILD_ENV}"
log_info "Model version: ${MODEL_VERSION}"

# Step 1: Check if models exist locally
log_step "Checking for local Ollama models..."
if [ -d "${PROJECT_ROOT}/ollama_models/models" ] && [ "$(ls -A ${PROJECT_ROOT}/ollama_models/models)" ]; then
    log_info "Local models found ($(du -sh ${PROJECT_ROOT}/ollama_models | cut -f1))"
else
    if [ "${SKIP_MODEL_DOWNLOAD}" = "true" ]; then
        log_info "Skipping model download (SKIP_MODEL_DOWNLOAD=true)"
    else
        log_step "Downloading models from GCP bucket..."
        "${SCRIPT_DIR}/gcp_models_sync.sh" download "${MODEL_VERSION}"
    fi
fi

# Step 2: Build Docker images
log_step "Building Docker images..."
cd "${PROJECT_ROOT}/docker/run"

if [ "${BUILD_ENV}" = "production" ]; then
    log_info "Building production images..."
    docker-compose build --no-cache
else
    log_info "Building development images..."
    docker-compose build
fi

# Step 3: Verify model integrity
log_step "Verifying model integrity..."
if [ -f "${PROJECT_ROOT}/ollama_models/model_manifest.json" ]; then
    log_info "Model manifest found:"
    cat "${PROJECT_ROOT}/ollama_models/model_manifest.json" | jq -r '.models[] | "\(.name) - \(.size)"' 2>/dev/null || cat "${PROJECT_ROOT}/ollama_models/model_manifest.json"
else
    log_info "No manifest found - generating..."
    "${SCRIPT_DIR}/gcp_models_sync.sh" manifest
fi

# Step 4: Start services
log_step "Starting services..."
docker-compose down 2>/dev/null || true
docker-compose up -d

# Step 5: Health check
log_step "Running health checks..."
sleep 5

# Check Ollama
if docker exec ollama ollama list &>/dev/null; then
    log_info "✓ Ollama service healthy"
    docker exec ollama ollama list
else
    log_info "⚠ Ollama service not ready yet"
fi

# Check Agent Jumbo
if curl -s http://localhost:50080 &>/dev/null; then
    log_info "✓ Agent Jumbo UI accessible at http://localhost:50080"
else
    log_info "⚠ Agent Jumbo UI not ready yet (may still be starting)"
fi

log_info "Build complete!"
log_info ""
log_info "Next steps:"
log_info "  - Access UI: http://localhost:50080"
log_info "  - View logs: docker-compose logs -f"
log_info "  - Upload models: ${SCRIPT_DIR}/gcp_models_sync.sh upload"
