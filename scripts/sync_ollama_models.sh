#!/bin/bash
# Ensure Ollama Model Persistence
# Run this once to sync host ollama models to project directory

set -e

SOURCE_DIR="${HOME}/.ollama"
TARGET_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/ollama_models"

echo "🔍 Ollama Model Sync Utility"
echo "============================"
echo ""
echo "Source: ${SOURCE_DIR}"
echo "Target: ${TARGET_DIR}"
echo ""

if [ ! -d "${SOURCE_DIR}" ]; then
    echo "✗ Source directory ${SOURCE_DIR} not found"
    echo "  Run 'ollama pull qwen2.5-coder:7b' on host first"
    exit 1
fi

if [ ! -d "${SOURCE_DIR}/models" ]; then
    echo "✗ No models found in ${SOURCE_DIR}"
    echo "  Run 'ollama pull qwen2.5-coder:7b' on host first"
    exit 1
fi

SOURCE_SIZE=$(du -sh "${SOURCE_DIR}" | cut -f1)
echo "Source size: ${SOURCE_SIZE}"
echo ""

read -p "Sync ${SOURCE_SIZE} to project? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled"
    exit 0
fi

echo "📦 Syncing models..."
rsync -av --progress "${SOURCE_DIR}/" "${TARGET_DIR}/"

echo ""
echo "✓ Sync complete!"
echo ""
echo "Models in project:"
ls -lh "${TARGET_DIR}/models/blobs/" 2>/dev/null | head -10 || echo "No blobs yet"

echo ""
echo "Next steps:"
echo "1. Restart containers: cd docker/run && docker-compose restart ollama"
echo "2. Verify model: docker exec ollama ollama list"
echo "3. Test Agent Jumbo: http://localhost:50080"
