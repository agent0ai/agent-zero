#!/bin/bash
# GCP Bucket Sync Script for Ollama Models
# Manages versioned model artifacts in GCP bucket

set -e

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODELS_DIR="${PROJECT_ROOT}/ollama_models"
GCP_BUCKET="${GCP_BUCKET:-gs://agent-jumbo-models}"
MODEL_VERSION="${MODEL_VERSION:-$(date +%Y%m%d-%H%M%S)}"
MANIFEST_FILE="${MODELS_DIR}/model_manifest.json"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if gcloud is installed
check_gcloud() {
    if ! command -v gcloud &> /dev/null; then
        log_error "gcloud CLI not found. Install from: https://cloud.google.com/sdk/docs/install"
        exit 1
    fi

    if ! command -v gsutil &> /dev/null; then
        log_error "gsutil not found. Install gcloud SDK properly."
        exit 1
    fi
}

# Generate model manifest
generate_manifest() {
    log_info "Generating model manifest..."

    cat > "${MANIFEST_FILE}" <<EOF
{
  "version": "${MODEL_VERSION}",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "models": [
EOF

    # Find all model manifests
    local first=true
    for manifest in $(find "${MODELS_DIR}/models/manifests" -type f 2>/dev/null); do
        local model_name=$(echo "$manifest" | sed "s|${MODELS_DIR}/models/manifests/registry.ollama.ai/library/||" | tr '/' ':')

        if [ "$first" = false ]; then
            echo "," >> "${MANIFEST_FILE}"
        fi
        first=false

        cat >> "${MANIFEST_FILE}" <<EOF
    {
      "name": "${model_name}",
      "path": "${manifest#$MODELS_DIR/}",
      "size": "$(du -sh "${MODELS_DIR}" | cut -f1)"
    }
EOF
    done

    cat >> "${MANIFEST_FILE}" <<EOF

  ],
  "total_size": "$(du -sh "${MODELS_DIR}" | cut -f1)"
}
EOF

    log_info "Manifest created at ${MANIFEST_FILE}"
    cat "${MANIFEST_FILE}"
}

# Upload models to GCP bucket
upload_models() {
    check_gcloud

    log_info "Uploading models to ${GCP_BUCKET}/${MODEL_VERSION}/"

    # Generate manifest first
    generate_manifest

    # Create versioned directory in bucket
    gsutil -m rsync -r -d "${MODELS_DIR}" "${GCP_BUCKET}/${MODEL_VERSION}/"

    # Upload manifest to root and versioned location
    gsutil cp "${MANIFEST_FILE}" "${GCP_BUCKET}/${MODEL_VERSION}/model_manifest.json"
    gsutil cp "${MANIFEST_FILE}" "${GCP_BUCKET}/latest_manifest.json"

    # Create 'latest' symlink metadata
    echo "${MODEL_VERSION}" | gsutil cp - "${GCP_BUCKET}/LATEST_VERSION"

    log_info "Upload complete! Version: ${MODEL_VERSION}"
    log_info "Models available at: ${GCP_BUCKET}/${MODEL_VERSION}/"
}

# Download models from GCP bucket
download_models() {
    check_gcloud

    local version="${1:-latest}"

    if [ "$version" = "latest" ]; then
        log_info "Fetching latest version..."
        version=$(gsutil cat "${GCP_BUCKET}/LATEST_VERSION" 2>/dev/null || echo "")

        if [ -z "$version" ]; then
            log_error "No latest version found in bucket"
            exit 1
        fi
    fi

    log_info "Downloading models version: ${version}"

    # Create models directory if it doesn't exist
    mkdir -p "${MODELS_DIR}"

    # Download models
    gsutil -m rsync -r -d "${GCP_BUCKET}/${version}/" "${MODELS_DIR}/"

    log_info "Download complete! Models available at ${MODELS_DIR}"

    # Show manifest
    if [ -f "${MANIFEST_FILE}" ]; then
        log_info "Model manifest:"
        cat "${MANIFEST_FILE}"
    fi
}

# List available versions
list_versions() {
    check_gcloud

    log_info "Available model versions in ${GCP_BUCKET}:"
    gsutil ls "${GCP_BUCKET}/" | grep -E '[0-9]{8}-[0-9]{6}' || log_warn "No versions found"

    echo ""
    log_info "Latest version:"
    gsutil cat "${GCP_BUCKET}/LATEST_VERSION" 2>/dev/null || log_warn "No latest version set"
}

# Clean old versions (keep last N versions)
clean_old_versions() {
    check_gcloud

    local keep_count="${1:-5}"

    log_info "Cleaning old versions (keeping last ${keep_count})..."

    # Get all versions sorted by date (newest first)
    local versions=$(gsutil ls "${GCP_BUCKET}/" | grep -E '[0-9]{8}-[0-9]{6}' | sort -r)
    local count=0

    for version_path in $versions; do
        count=$((count + 1))

        if [ $count -gt $keep_count ]; then
            log_warn "Removing old version: ${version_path}"
            gsutil -m rm -r "${version_path}"
        fi
    done

    log_info "Cleanup complete"
}

# Main command dispatcher
case "${1:-help}" in
    upload)
        upload_models
        ;;
    download)
        download_models "${2:-latest}"
        ;;
    list)
        list_versions
        ;;
    clean)
        clean_old_versions "${2:-5}"
        ;;
    manifest)
        generate_manifest
        ;;
    help|*)
        cat <<EOF
Usage: $0 <command> [options]

Commands:
    upload              Upload models to GCP bucket with versioning
    download [version]  Download models from GCP bucket (default: latest)
    list                List all available versions in bucket
    clean [keep_count]  Remove old versions (default: keep last 5)
    manifest            Generate model manifest without uploading
    help                Show this help message

Environment Variables:
    GCP_BUCKET          GCS bucket path (default: gs://agent-jumbo-models)
    MODEL_VERSION       Version tag (default: timestamp YYYYMMDD-HHMMSS)

Examples:
    # Upload current models
    $0 upload

    # Download latest models
    $0 download

    # Download specific version
    $0 download 20260113-220000

    # List all versions
    $0 list

    # Clean old versions (keep last 3)
    $0 clean 3
EOF
        ;;
esac
