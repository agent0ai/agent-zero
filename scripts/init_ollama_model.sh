#!/bin/bash
# Ollama Model Initialization Script
# Ensures qwen2.5-coder:7b is pulled and ready before Agent Jumbo starts

set -e

REQUIRED_MODEL="qwen2.5-coder:7b"
OLLAMA_HOST="${OLLAMA_HOST:-http://localhost:11434}"
MAX_RETRIES=30
RETRY_DELAY=2

echo "🔍 Checking Ollama service availability..."

# Wait for Ollama to be ready
for i in $(seq 1 $MAX_RETRIES); do
    if curl -s "${OLLAMA_HOST}/api/tags" > /dev/null 2>&1; then
        echo "✓ Ollama service is ready"
        break
    fi

    if [ $i -eq $MAX_RETRIES ]; then
        echo "✗ Ollama service not available after ${MAX_RETRIES} attempts"
        exit 1
    fi

    echo "  Waiting for Ollama... (attempt $i/$MAX_RETRIES)"
    sleep $RETRY_DELAY
done

# Check if model exists
echo "🔍 Checking for model: ${REQUIRED_MODEL}"
if ollama list | grep -q "${REQUIRED_MODEL}"; then
    echo "✓ Model ${REQUIRED_MODEL} is already available"
    ollama list
    exit 0
fi

# Model doesn't exist - check if we have model files
MODEL_MANIFEST="/root/.ollama/models/manifests/registry.ollama.ai/library/qwen2.5-coder/7b"
if [ -f "$MODEL_MANIFEST" ]; then
    echo "📦 Model files found in volume, attempting to register..."

    # The manifest exists but Ollama doesn't see it
    # This happens when files are copied externally
    # We need to trigger Ollama to recognize them

    # Try to run the model to trigger registration
    echo "🔄 Attempting to load model from existing files..."
    timeout 60 ollama run "${REQUIRED_MODEL}" "test" > /dev/null 2>&1 || true

    # Check again
    if ollama list | grep -q "${REQUIRED_MODEL}"; then
        echo "✓ Model registered successfully from existing files"
        ollama list
        exit 0
    fi
fi

# If we get here, we need to pull the model
echo "📥 Pulling model: ${REQUIRED_MODEL}"
echo "   This may take several minutes (4.7 GB download)..."

# Pull with progress
ollama pull "${REQUIRED_MODEL}"

echo "✓ Model ${REQUIRED_MODEL} is ready"
ollama list
