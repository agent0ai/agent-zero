# Ollama Models Directory

This directory contains Ollama model data (blobs, manifests, etc.) for Agent Jumbo.

## ⚠️ Models are NOT stored in Git

Model files are **excluded from Git** due to their large size (4+ GB). Instead:

- **Models are versioned in GCP Cloud Storage bucket**: `gs://agent-jumbo-models`
- **Download models before building**: `./scripts/gcp_models_sync.sh download`
- **Upload new model versions**: `./scripts/gcp_models_sync.sh upload`

## Quick Start

### Download Latest Models

```bash
./scripts/gcp_models_sync.sh download
```

### Download Specific Version

```bash
./scripts/gcp_models_sync.sh download 20260113-220000
```

### List Available Versions

```bash
./scripts/gcp_models_sync.sh list
```

### Upload Current Models

```bash
./scripts/gcp_models_sync.sh upload
```

## Build Integration

The build script automatically handles model download:

```bash
# Build with automatic model download
./scripts/build.sh

# Build without downloading models (use local)
SKIP_MODEL_DOWNLOAD=true ./scripts/build.sh

# Build with specific model version
MODEL_VERSION=20260113-220000 ./scripts/build.sh
```

## Directory Structure

```
ollama_models/
├── models/          # Ollama model manifests (gitignored)
├── blobs/           # Model binary blobs (gitignored)
├── model_manifest.json  # Version metadata (tracked in git)
└── README.md        # This file (tracked in git)
```

## Model Manifest

The `model_manifest.json` file contains:

- Version timestamp
- List of models with sizes
- Total size
- Model paths

This file **IS tracked in Git** to document which models are expected.

## GCP Bucket Structure

```
gs://agent-jumbo-models/
├── 20260113-220000/     # Versioned model snapshots
│   ├── models/
│   ├── blobs/
│   └── model_manifest.json
├── 20260113-210000/     # Previous version
├── LATEST_VERSION       # Points to current version
└── latest_manifest.json # Latest manifest for quick reference
```

## Current Models

- **qwen2.5-coder:7b** - Primary coding model (4.4 GB)

## Adding New Models

1. Pull model with Ollama on host:

   ```bash
   ollama pull <model-name>
   ```

2. Copy to project:

   ```bash
   cp -r ~/.ollama/* ./ollama_models/
   ```

3. Upload to GCP:

   ```bash
   ./scripts/gcp_models_sync.sh upload
   ```

## CI/CD Integration

Add to your CI/CD pipeline:

```yaml
- name: Download Ollama Models
  run: |
    ./scripts/gcp_models_sync.sh download

- name: Build Agent Jumbo
  run: |
    ./scripts/build.sh
```

## Environment Variables

- `GCP_BUCKET` - GCS bucket path (default: `gs://agent-jumbo-models`)
- `MODEL_VERSION` - Specific version to download (default: `latest`)
- `SKIP_MODEL_DOWNLOAD` - Skip download in build (default: `false`)

## Troubleshooting

### Models not loading in Ollama

```bash
# Restart Ollama container
docker restart ollama

# Check models directory is mounted
docker exec ollama ls -la /root/.ollama/models/
```

### Download fails

```bash
# Check GCP authentication
gcloud auth list

# Verify bucket access
gsutil ls gs://agent-jumbo-models/
```

### Clean up old versions

```bash
# Keep last 5 versions, delete older
./scripts/gcp_models_sync.sh clean 5
```
