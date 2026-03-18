---
    title: "🔒 Security: Remove dangerous deserialization in FAISS"
    labels: "security, critical, memory"
    ---

    ## Problem Statement

    `Memory.initialize()` uses FAISS with `allow_dangerous_deserialization=True`, which allows arbitrary code execution through malicious pickle files.

    ## Vulnerability Details

    ```python
    db = MyFaiss.load_local(
        folder_path=db_dir,
        embeddings=embedder,
        allow_dangerous_deserialization=True,  # ⚠️ DANGEROUS!
        distance_strategy=DistanceStrategy.COSINE,
    )
    ```

    If an attacker can write to the memory directory (e.g., via malicious knowledge import, backup restore, or compromised agent), they can execute arbitrary code when the vector DB loads.

    ## Attack Scenarios

    1. **Malicious Knowledge Import**
       - Attacker provides crafted `.faiss` files disguised as knowledge base
       - Loaded on next agent startup → RCE

    2. **Backup Poisoning**
       - Attacker compromises backup storage
       - Replaces `index.faiss` with malicious pickle
       - Restore → code execution

    3. **Compromised MCP Server**
       - Malicious MCP server returns file paths to attack
       - Agent loads those FAISS indexes → RCE

    ## Proposed Solutions

    ### Option A: Use Safe FAISS (Recommended)
    FAISS 1.7+ supports safe deserialization via `faiss.serde.read_index`:

    ```python
    from faiss import serde

    # Safe loading (no pickle)
    db = serde.read_index(folder_path)
    ```

    **Challenge:** Need to check compatibility with `langchain_community.vectorstores.FAISS`

    ### Option B: Switch to Alternative Vector DB
    - **ChromaDB** (already in code as commented import)
    - **Qdrant** (binary protocol, no pickle)
    - **Weaviate** (gRPC, safe by default)
    - **pgvector** (PostgreSQL extension)

    ### Option C: Validate FAISS files before loading
    - Check SHA256 of index.faiss against known good values
    - Reject files with unexpected size/structure
    - **Not recommended** - defense in depth only, not complete mitigation

    ## Implementation Plan (Option A)

    1. **Research faiss.serde compatibility**
       - Test if `serde.read_index()` works with existing FAISS usage
       - Check if embeddings need to be re-attached after load
       - Verify performance parity

    2. **If compatible, replace call:**
       ```python
       # Old
       db = MyFaiss.load_local(..., allow_dangerous_deserialization=True)
   
       # New
       db = MyFaiss(); db = faiss.serde.read_index(folder_path, db)
       # OR
       db = MyFaiss.load_local(folder_path, embeddings=embedder, allow_dangerous_deserialization=False)
       ```

    3. **If not compatible, migrate to ChromaDB:**
       - Implement `chromadb` backend
       - Provide migration tool: FAISS → ChromaDB
       - Update all `Memory` methods to use ChromaDB client

    ## Testing Requirements

    - [ ] Verify FAISS indexes load without code execution risk
    - [ ] Ensure semantic search still works correctly
    - [ ] Performance benchmarking (query latency)
    - [ ] Compatibility with existing memory data
    - [ ] Migration tool tested on large indexes (>100k vectors)

    ## Breaking Changes

    - **Potential:** Existing memory indexes may need re-creation
    - **Mitigation:** Provide migration script that:
      1. Loads old index with safe method (if possible)
      2. Exports vectors + metadata
      3. Re-imports to new safe backend

    ## Related Issues

    - **Part of larger security hardening initiative**
    - Related to **Container security** (defense in depth)
    - Should be done before **public deployments**

    ## References

    - [FAISS GitHub - Security Warning](https://github.com/facebookresearch/faiss)
    - [CVE-2023-xxxx - FAISS pickle deserialization](https://cve.mitre.org/)
    - [OWASP - Deserialization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Deserialization_Cheat_Sheet.html)

    ---
    *This is a CRITICAL security issue that should be patched immediately.*
    