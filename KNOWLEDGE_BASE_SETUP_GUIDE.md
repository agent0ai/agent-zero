# 🎯 Agent Zero Knowledge Base - Final Setup Guide

## ✅ What We've Accomplished

### Phase 1: Infrastructure ✅ COMPLETE
- Docker stack running (Agent Zero, Qdrant, Unity MCP, Redis)
- Qdrant accessible at http://localhost:6333
- Collections list: Currently empty (ready to populate)

### Phase 2: Professional Architecture ✅ DESIGNED
Based on "Architectural Strategy for Unity Documentation RAG Systems":

**Key Components Created:**
1. `build_unity_kb.py` - Unity-aware metadata scanner
   - Extracts GUIDs from .meta files
   - Finds Assembly Definitions  
   - Categorizes code (runtime/editor/test)
   - Parses class names

2. `setup_qdrant_collection.py` - Hybrid search collection setup
   - Dense vectors (384D, Cosine)
   - Sparse vectors (keyword matching)
   - Payload indexes for filtering

3. `ingest_to_qdrant.py` - Complete ingestion pipeline
   - C#-aware chunking
   - Context enrichment
   - Deterministic UUID generation
   - Batch upload to Qdrant

4. `test_search.py` - Verification and testing

## 🚀 How to Complete the Setup

### Option 1: Using Agent Zero's UI (Recommended)

1. Open Agent Zero: http://localhost:50001

2. Ask Agent Zero to run these commands:

```
Step 1: Install required Python packages
!pip install requests sentence-transformers scikit-learn

Step 2: Scan the Unity project
!python3 /host_data/build_unity_kb.py

Step 3: Create Qdrant collection
!python3 /host_data/setup_qdrant_collection.py

Step 4: Ingest documents
!python3 /host_data/ingest_to_qdrant.py

Step 5: Test search
!python3 /host_data/test_search.py
```

### Option 2: Manual Execution

```powershell
# Copy scripts to container
docker cp d:\GithubRepos\agent-zero\*.py agent-zero-unity:/a0/

# Enter container
docker exec -it agent-zero-unity bash

# Install deps (if pip is available)
pip3 install requests sentence-transformers scikit-learn

# Run pipeline
python3 /a0/build_unity_kb.py
python3 /a0/setup_qdrant_collection.py  
python3 /a0/ingest_to_qdrant.py
python3 /a0/test_search.py
```

### Option 3: Use Agent Zero's Native Tools

Agent Zero has built-in knowledge base tools. Simply ask it:

```
"Please index all C# files from /a0/usr/projects/unitymlcreator into Qdrant. 
Use the embedding model 'sentence-transformers/all-MiniLM-L6-v2' and create 
a collection called 'unity_project_kb'. Make sure to extract Unity GUIDs 
from .meta files and assembly context from .asmdef files."
```

## 📊 Expected Results

Once complete, you'll have:

- **Collection**: `unity_project_kb`  
- **Points**: ~500-2000 (depends on project size)
- **Vectors**: Dense (384D) + Sparse (keyword)
- **Indexes**: asset_guid, assembly_name, code_type, class_name

### Searchable by:

1. **Semantic queries**: "player movement code"
2. **Assembly scope**: Filter to specific assemblies
3. **Code type**: Filter runtime vs editor code  
4. **Exact keywords**: Find specific variable/class names

## 🔍 Testing the Knowledge Base

### Via Qdrant Dashboard
- Open: http://localhost:6333/dashboard
- Browse collection: `unity_project_kb`
- View points and metadata

### Via Agent Zero
Ask questions like:
- "Show me all player controller code"
- "Find editor tools for level design"
- "Where is PlayerMovement class defined?"
- "Show all code in the GameCreator.Runtime.Core assembly"

## 📁 Files Reference

| File | Purpose | Location |
|------|---------|----------|
| `build_unity_kb.py` | Scan & extract metadata | `/host_data/` or `/a0/` |
| `setup_qdrant_collection.py` | Create collection | `/host_data/` or `/a0/` |
| `ingest_to_qdrant.py` | Embed & upload | `/host_data/` or `/a0/` |
| `test_search.py` | Verify search | `/host_data/` or `/a0/` |
| `run_kb_pipeline.sh` | Complete pipeline | `/host_data/` or `/a0/` |

## 🎓 Architecture Details

Based on research from "Qdrant Strategy for Unity Knowledge Base.txt":

### Metadata Schema
```json
{
  "asset_guid": "af75e2b85ae3e5c469fc1519863be5ef",
  "file_path": "Assets/Scripts/PlayerController.cs",
  "assembly_name": "Game.Gameplay", 
  "code_type": "runtime",
  "class_name": "PlayerController",
  "chunk_index": 0,
  "content_hash": "a7b3c2d1e4f5"
}
```

### Chunking Strategy
- Respects C# semantic boundaries
- Keeps classes/methods intact
- Adds context headers to chunks
- Max chunk size: ~1000 tokens

### UUID Generation
```python
uuid5(NAMESPACE_DNS, asset_guid + "_" + chunk_index)
```
This ensures idempotent re-indexing.

## ⚡ Next Steps

1. Complete the ingestion (choose Option 1, 2, or 3 above)
2. Verify via Qdrant Dashboard
3. Test search queries via Agent Zero
4. (Optional) Upgrade to Voyage-Code-2 embeddings for better accuracy

## 🔧 Troubleshooting

### "No module named requests"
The agent-zero-unity container needs Python packages installed. Use Agent Zero's UI to run `!pip install` commands.

### "VOYAGE_API_KEY not found"
We're using sentence-transformers (local, free) instead. Voyage is optional for better accuracy.

### "Collection not found"
Run `setup_qdrant_collection.py` first to create the collection.

---

**Status**: Ready for ingestion! All scripts created and copied to container.  
**Next**: Run the pipeline via Agent Zero's UI (Option 1 recommended)
