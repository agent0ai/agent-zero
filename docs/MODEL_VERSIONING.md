# Agent Jumbo - Model Management & GCP Deployment Guide

## ✅ Setup Complete

Your Ollama models are now:

- ✅ Stored locally in `ollama_models/` directory (4.4 GB)
- ✅ Excluded from Git (only manifest tracked)
- ✅ Ready for GCP bucket versioning
- ✅ Integrated with Docker build process

## 🚀 Quick Commands

### Build & Run

```bash
# Full build with automatic model handling
./scripts/build.sh

# Access Agent Jumbo
http://localhost:50080
```

### GCP Model Sync

```bash
# Upload current models to GCP bucket (first time setup)
./scripts/gcp_models_sync.sh upload

# Download models from GCP (for new environments)
./scripts/gcp_models_sync.sh download

# List all versions in bucket
./scripts/gcp_models_sync.sh list

# Clean old versions (keep last 5)
./scripts/gcp_models_sync.sh clean 5
```

## 📦 Model Versioning Strategy

### Current Setup

- **Model Location**: `./ollama_models/` (4.4 GB)
- **Model Version**: `20260113-184641`
- **Included Models**: qwen2.5-coder:7b
- **GCP Bucket**: `gs://agent-jumbo-models` (configurable)

### Version Format

Versions use timestamp: `YYYYMMDD-HHMMSS`

- Example: `20260113-184641` = Jan 13, 2026 at 18:46:41

### What's Tracked in Git

- ✅ `ollama_models/model_manifest.json` - Version metadata
- ✅ `ollama_models/README.md` - Documentation
- ✅ `ollama_models/.gitkeep` - Directory structure
- ❌ `ollama_models/models/` - Model files (too large)
- ❌ `ollama_models/blobs/` - Binary data (too large)

## 🔧 GCP Bucket Setup

### One-Time Setup

1. **Create GCP Bucket**

   ```bash
   # Set your project
   gcloud config set project YOUR_PROJECT_ID

   # Create bucket (choose region close to you)
   gsutil mb -l us-central1 gs://agent-jumbo-models

   # Or use custom name
   export GCP_BUCKET=gs://your-custom-bucket-name
   ```

2. **Upload Initial Models**

   ```bash
   ./scripts/gcp_models_sync.sh upload
   ```

3. **Verify Upload**

   ```bash
   ./scripts/gcp_models_sync.sh list
   ```

### Team Workflow

**Developer 1** (You - has models locally):

```bash
# Upload to bucket
./scripts/gcp_models_sync.sh upload

# Commit code changes (models excluded by .gitignore)
git add .
git commit -m "Add model versioning system"
git push
```

**Developer 2** (New team member):

```bash
# Clone repo
git clone <repo-url>
cd agent-jumbo

# Download models from GCP
./scripts/gcp_models_sync.sh download

# Build and run
./scripts/build.sh
```

## 🏗️ CI/CD Integration

### GitHub Actions Example

```yaml
name: Build Agent Jumbo

on: [push]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Authenticate to GCP
        uses: google-github-actions/auth@v1
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}

      - name: Download Models
        run: |
          ./scripts/gcp_models_sync.sh download

      - name: Build
        run: |
          ./scripts/build.sh
```

### GitLab CI Example

```yaml
build:
  image: google/cloud-sdk:alpine
  before_script:
    - echo $GCP_SA_KEY | base64 -d > /tmp/gcp-key.json
    - gcloud auth activate-service-account --key-file=/tmp/gcp-key.json
  script:
    - ./scripts/gcp_models_sync.sh download
    - ./scripts/build.sh
```

## 📝 Build Script Options

```bash
# Standard build
./scripts/build.sh

# Skip model download (use existing local models)
SKIP_MODEL_DOWNLOAD=true ./scripts/build.sh

# Use specific model version
MODEL_VERSION=20260113-184641 ./scripts/build.sh

# Production build (no cache)
BUILD_ENV=production ./scripts/build.sh

# Custom GCP bucket
GCP_BUCKET=gs://my-models ./scripts/build.sh
```

## 🔄 Model Update Workflow

When you need to update/add models:

1. **Pull new model on host**

   ```bash
   ollama pull new-model:latest
   ```

2. **Copy to project**

   ```bash
   cp -r ~/.ollama/* ./ollama_models/
   ```

3. **Generate new manifest**

   ```bash
   ./scripts/gcp_models_sync.sh manifest
   ```

4. **Upload new version to GCP**

   ```bash
   ./scripts/gcp_models_sync.sh upload
   ```

5. **Commit manifest update**

   ```bash
   git add ollama_models/model_manifest.json
   git commit -m "Update models to include new-model:latest"
   git push
   ```

## 🗑️ Storage Management

### Local Storage

```bash
# Check model size
du -sh ollama_models/

# Clean up (will re-download from GCP)
rm -rf ollama_models/models ollama_models/blobs
./scripts/gcp_models_sync.sh download
```

### GCP Storage

```bash
# List versions with sizes
gsutil du -sh gs://agent-jumbo-models/*

# Remove specific version
gsutil -m rm -r gs://agent-jumbo-models/20260113-184641

# Keep last 5 versions
./scripts/gcp_models_sync.sh clean 5
```

## 🔍 Troubleshooting

### Models not showing in Ollama

```bash
# Check mount
docker exec ollama ls -la /root/.ollama/models/

# Restart Ollama
docker restart ollama
docker exec ollama ollama list
```

### GCP authentication issues

```bash
# Check auth
gcloud auth list

# Re-authenticate
gcloud auth login

# Service account (CI/CD)
gcloud auth activate-service-account --key-file=key.json
```

### Download fails

```bash
# Check bucket exists
gsutil ls gs://agent-jumbo-models/

# Check permissions
gsutil iam get gs://agent-jumbo-models/

# Manual download
gsutil -m rsync -r gs://agent-jumbo-models/latest/ ./ollama_models/
```

## 💡 Cost Optimization

### GCP Storage Costs

- Standard Storage: ~$0.02/GB/month
- 4.4 GB model: ~$0.09/month
- 10 versions: ~$0.90/month

### Optimization Tips

1. **Use Nearline/Coldline for old versions**

   ```bash
   gsutil rewrite -s nearline gs://agent-jumbo-models/old-version/**
   ```

2. **Auto-delete old versions**
   - Set lifecycle policy on bucket
   - Or use `./scripts/gcp_models_sync.sh clean 3`

3. **Regional buckets**
   - Place bucket in same region as compute
   - Reduces egress costs

## 📚 Additional Resources

- **GCP Bucket**: See `scripts/gcp_models_sync.sh --help`
- **Build Script**: See `scripts/build.sh`
- **Model Directory**: See `ollama_models/README.md`
- **Docker Compose**: See `docker/run/docker-compose.yml`

## ✨ Summary

You now have a complete model versioning system:

1. ✅ Models stored in project (not in Git)
2. ✅ GCP bucket for version control
3. ✅ Automated build integration
4. ✅ Team-friendly workflow
5. ✅ CI/CD ready

**Next Step**: Upload to GCP bucket

```bash
./scripts/gcp_models_sync.sh upload
```
