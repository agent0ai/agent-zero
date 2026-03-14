# 🚀 Agent Jumbo - Quick Reference

## ✅ System Status

**All Systems Operational**

- ✓ Docker containers running
- ✓ Agent Jumbo UI: <http://localhost:50080>
- ✓ Ollama models: 4.4GB in project
- ✓ Portfolio Manager tool loaded
- ✓ Property Manager tool loaded
- ✓ Database persistence configured

## 📋 Common Commands

### Daily Operations

```bash
# Start everything
cd docker/run && docker-compose up -d

# Stop everything
cd docker/run && docker-compose down

# View logs
cd docker/run && docker-compose logs -f

# Restart a service
docker restart ollama
docker restart agent-jumbo

# Check status
./scripts/validate.sh
```

### Model Management

```bash
# Upload models to GCP (first time)
./scripts/gcp_models_sync.sh upload

# Download models from GCP (new machine)
./scripts/gcp_models_sync.sh download

# List versions in GCP
./scripts/gcp_models_sync.sh list

# Clean old versions (keep last 5)
./scripts/gcp_models_sync.sh clean 5
```

### Build & Deploy

```bash
# Full build with model handling
./scripts/build.sh

# Build without downloading models
SKIP_MODEL_DOWNLOAD=true ./scripts/build.sh

# Build with specific model version
MODEL_VERSION=20260113-184641 ./scripts/build.sh
```

## 🛠️ Tools Available

### Portfolio Manager

**Purpose**: Scan, analyze, and manage your code projects for sale

**Key Actions**:

- `scan` - Scan directory for projects
- `list` - List all projects in portfolio
- `analyze` - Deep analysis of project quality
- `create_product` - Convert project to sellable product
- `pipeline` - Manage sales pipeline

**Example**:
> "Scan /home/webemo-aaron/projects for my portfolio"

### Property Manager

**Purpose**: Manage West Bethel Motel and rental properties

**Key Actions**:

- `setup_initial` - Initialize West Bethel Motel
- `add_property` - Add new rental property
- `add_tenant` - Add tenant to unit
- `record_payment` - Record rent payment
- `maintenance_request` - Create maintenance ticket
- `financial_summary` - View income/expenses

**Example**:
> "Initialize West Bethel Motel with 12 units"

## 📁 Project Structure

```
agent-jumbo/
├── ollama_models/          # Ollama models (4.4GB, not in Git)
│   ├── models/             # Model manifests
│   ├── blobs/              # Model binaries
│   └── model_manifest.json # Version info (tracked in Git)
├── scripts/
│   ├── build.sh            # Build with model handling
│   ├── gcp_models_sync.sh  # Upload/download to GCP
│   └── validate.sh         # Check deployment status
├── docker/run/
│   ├── docker-compose.yml  # Container orchestration
│   └── agent-jumbo/data/    # SQLite databases (persistent)
├── python/tools/
│   ├── portfolio_manager_tool.py  # 17KB
│   └── property_manager_tool.py   # 29KB
├── instruments/custom/
│   ├── portfolio_manager/  # Database + scanner logic
│   └── property_manager/   # Database + operations logic
└── docs/
    ├── MODEL_VERSIONING.md    # GCP bucket guide
    ├── portfolio_manager.md   # Portfolio docs
    ├── property_manager.md    # Property docs
    └── TESTING_GUIDE.md       # Test procedures
```

## 🔧 Troubleshooting

### Ollama models not loading

```bash
# Check mount
docker exec ollama ls -la /root/.ollama/models/

# Restart and wait for model verification
docker restart ollama
sleep 30
docker exec ollama ollama list
```

### Agent Jumbo UI not accessible

```bash
# Check logs
docker logs agent-jumbo

# Restart
docker restart agent-jumbo
```

### Database not persisting

```bash
# Check volume
docker volume inspect agent_jumbo_data

# Check mount
docker exec agent-jumbo ls -la /a0/data/
```

### GCP sync fails

```bash
# Check authentication
gcloud auth list

# Re-authenticate
gcloud auth login

# Check bucket
gsutil ls gs://agent-jumbo-models/
```

## 📊 Testing Checklist

### Portfolio Manager

- [ ] Scan a directory with projects
- [ ] View project list
- [ ] Analyze project quality score
- [ ] Create product from project
- [ ] Export portfolio report

### Property Manager

- [ ] Initialize West Bethel Motel
- [ ] Add 3 house properties
- [ ] Add tenants to units
- [ ] Record rent payments
- [ ] Create maintenance request
- [ ] View financial summary

### Infrastructure

- [ ] Restart containers - verify models persist
- [ ] Create test database - verify data persists
- [ ] Upload models to GCP bucket
- [ ] Download models on clean system

## 🌐 Access Points

- **Agent Jumbo UI**: <http://localhost:50080>
- **Ollama API**: <http://localhost:11434>
- **Model Manifest**: `ollama_models/model_manifest.json`
- **Databases**: `docker/run/agent-jumbo/data/`

## 📝 Important Notes

1. **Models are NOT in Git** - They're in `ollama_models/` (gitignored) and versioned in GCP bucket
2. **Download before building** - New machines need: `./scripts/gcp_models_sync.sh download`
3. **Databases persist** - SQLite files in volume survive container restarts
4. **Tools auto-load** - Agent Jumbo discovers `python/tools/*.py` automatically

## 🎯 Next Actions

1. **Test the UI**: <http://localhost:50080>
2. **Initialize Properties**: "Setup West Bethel Motel with 12 units"
3. **Scan Portfolio**: Point at your projects folder
4. **Upload Models**: `./scripts/gcp_models_sync.sh upload`

---

**Current Version**: 20260113-184641
**Model**: qwen2.5-coder:7b (4.4GB) via Ollama (local)
**Provider**: Ollama at <http://ollama:11434>
**Status**: ✅ Ready for testing

## 📖 Additional Documentation

- **Ollama & Qwen Setup**: See `docs/OLLAMA_QWEN_CONFIG.md`
- **Model Versioning**: See `docs/MODEL_VERSIONING.md`
- **Testing Guide**: See `docs/TESTING_GUIDE.md`
