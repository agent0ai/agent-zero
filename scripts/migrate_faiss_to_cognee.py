#!/usr/bin/env python3
"""
Migration script: FAISS -> Cognee

Idempotent migration that preserves all original data and tracks progress
per-document. Safe to interrupt and restart -- will skip already migrated items.

Auto-runs on first startup via initialize.py. Can also be run manually:
    python scripts/migrate_faiss_to_cognee.py [--dry-run] [--verify] [--force]

Flags:
    --dry-run   Scan and report what would be migrated without making changes
    --verify    After migration, run verification searches
    --force     Re-migrate even if state file says complete
"""

import asyncio
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from python.helpers.cognee_init import configure_cognee

MIGRATION_STATE_FILE = "usr/cognee_migration_state.json"


def _abs(rel_path: str) -> str:
    from python.helpers import files
    return files.get_abs_path(rel_path)


def load_state(base_dir: str) -> dict:
    state_path = os.path.join(base_dir, MIGRATION_STATE_FILE)
    if os.path.exists(state_path):
        with open(state_path, "r") as f:
            return json.load(f)
    return {"version": 1, "indices": {}, "completed": False}


def save_state(base_dir: str, state: dict):
    state_path = os.path.join(base_dir, MIGRATION_STATE_FILE)
    os.makedirs(os.path.dirname(state_path), exist_ok=True)
    tmp_path = state_path + ".tmp"
    with open(tmp_path, "w") as f:
        json.dump(state, f, indent=2)
    os.replace(tmp_path, state_path)


def _is_backup_dir(name: str) -> bool:
    return name.endswith("_faiss_backup")


def find_faiss_indices(base_dir: str) -> list[dict]:
    indices = []

    global_memory = os.path.join(base_dir, "usr", "memory")
    if os.path.exists(global_memory):
        for subdir in os.listdir(global_memory):
            if _is_backup_dir(subdir):
                continue
            subdir_path = os.path.join(global_memory, subdir)
            if not os.path.isdir(subdir_path):
                continue
            index_path = os.path.join(subdir_path, "index.faiss")
            if os.path.isfile(index_path):
                indices.append({
                    "type": "global",
                    "subdir": subdir,
                    "memory_subdir": subdir,
                    "db_dir": subdir_path,
                    "index_path": index_path,
                })

    projects_dir = os.path.join(base_dir, "usr", "projects")
    if os.path.exists(projects_dir):
        for project_name in os.listdir(projects_dir):
            db_dir = os.path.join(
                projects_dir, project_name, ".a0proj", "memory"
            )
            index_path = os.path.join(db_dir, "index.faiss")
            if os.path.isfile(index_path):
                indices.append({
                    "type": "project",
                    "subdir": f"projects/{project_name}",
                    "memory_subdir": f"projects/{project_name}",
                    "project_name": project_name,
                    "db_dir": db_dir,
                    "index_path": index_path,
                })

    # Fallback: if originals were deleted, look for backups
    for backup_root in [
        os.path.join(base_dir, "usr", "memory_faiss_backup"),
        os.path.join(base_dir, "usr", "memory"),
    ]:
        if not os.path.exists(backup_root):
            continue
        for subdir in os.listdir(backup_root):
            if not _is_backup_dir(subdir) and backup_root.endswith("memory"):
                continue
            subdir_path = os.path.join(backup_root, subdir)
            if not os.path.isdir(subdir_path):
                continue
            index_path = os.path.join(subdir_path, "index.faiss")
            if not os.path.isfile(index_path):
                continue
            original_subdir = subdir.removesuffix("_faiss_backup")
            already = any(i["memory_subdir"] == original_subdir for i in indices)
            if not already:
                indices.append({
                    "type": "global_backup",
                    "subdir": original_subdir,
                    "memory_subdir": original_subdir,
                    "db_dir": subdir_path,
                    "index_path": index_path,
                })

    return indices


def load_faiss_db(db_dir: str) -> dict | None:
    """Load FAISS index. Returns dict of docs, or None if loading failed (missing deps, errors)."""
    try:
        from langchain.embeddings import CacheBackedEmbeddings
        from langchain.storage import LocalFileStore
        from langchain_community.vectorstores import FAISS
        from langchain_community.vectorstores.utils import DistanceStrategy
    except ImportError:
        print(f"  ERROR: faiss-cpu not installed, cannot load {db_dir}")
        print(f"  Install with: pip install faiss-cpu langchain-community")
        return None

    embedding_meta_path = os.path.join(db_dir, "embedding.json")
    if not os.path.exists(embedding_meta_path):
        print(f"  WARNING: No embedding.json in {db_dir}, skipping")
        return {}

    try:
        with open(embedding_meta_path) as f:
            embedding_meta = json.load(f)

        provider = embedding_meta["model_provider"]
        model_name = embedding_meta["model_name"]

        import models
        embedding_model = models.get_embedding_model(provider, model_name)

        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(db_dir)))
        em_dir = os.path.join(base_dir, "tmp", "memory", "embeddings")
        os.makedirs(em_dir, exist_ok=True)
        store = LocalFileStore(em_dir)

        from python.helpers import files
        embeddings_model_id = files.safe_file_name(provider + "_" + model_name)
        embedder = CacheBackedEmbeddings.from_bytes_store(
            embedding_model, store, namespace=embeddings_model_id
        )

        db = FAISS.load_local(
            folder_path=db_dir,
            embeddings=embedder,
            allow_dangerous_deserialization=True,
            distance_strategy=DistanceStrategy.COSINE,
        )

        return db.docstore._dict
    except Exception as e:
        print(f"  ERROR loading FAISS from {db_dir}: {e}")
        return None


def subdir_to_dataset(memory_subdir: str) -> str:
    return memory_subdir.replace("/", "_").replace(" ", "_").lower()


async def migrate_index(
    index_info: dict,
    state: dict,
    base_dir: str,
    dry_run: bool = False,
) -> dict:
    import cognee

    memory_subdir = index_info["memory_subdir"]
    db_dir = index_info["db_dir"]
    dataset_base = subdir_to_dataset(memory_subdir)
    index_key = f"{index_info['type']}:{memory_subdir}"

    index_state = state["indices"].get(index_key, {
        "status": "pending",
        "migrated_doc_ids": [],
        "total": 0,
        "errors": [],
    })

    if index_state.get("status") == "complete":
        print(f"\n  SKIP (already complete): {memory_subdir}")
        return {
            "subdir": memory_subdir,
            "total": index_state["total"],
            "migrated": len(index_state["migrated_doc_ids"]),
            "skipped": True,
        }

    print(f"\n{'[DRY RUN] ' if dry_run else ''}Migrating: {memory_subdir}")
    print(f"  DB dir: {db_dir}")

    all_docs = load_faiss_db(db_dir)
    if all_docs is None:
        print(f"  FAILED to load FAISS — will retry on next startup")
        index_state["status"] = "error"
        state["indices"][index_key] = index_state
        if not dry_run:
            save_state(base_dir, state)
        return {"subdir": memory_subdir, "total": 0, "migrated": 0, "skipped": False}
    if not all_docs:
        print(f"  No documents found, marking complete")
        index_state["status"] = "complete"
        index_state["total"] = 0
        state["indices"][index_key] = index_state
        if not dry_run:
            save_state(base_dir, state)
        return {"subdir": memory_subdir, "total": 0, "migrated": 0, "skipped": False}

    already_migrated = set(index_state.get("migrated_doc_ids", []))
    index_state["total"] = len(all_docs)

    by_area: dict[str, list] = {}
    for doc_id, doc in all_docs.items():
        if doc_id in already_migrated:
            continue
        area = doc.metadata.get("area", "main")
        if area not in by_area:
            by_area[area] = []
        by_area[area].append((doc_id, doc))

    pending = sum(len(docs) for docs in by_area.values())
    print(f"  Total: {len(all_docs)}, already migrated: {len(already_migrated)}, pending: {pending}")

    if pending == 0:
        index_state["status"] = "complete"
        state["indices"][index_key] = index_state
        if not dry_run:
            save_state(base_dir, state)
        return {
            "subdir": memory_subdir,
            "total": len(all_docs),
            "migrated": len(already_migrated),
            "skipped": False,
        }

    migrated_this_run = 0

    for area, docs in by_area.items():
        dataset_name = f"{dataset_base}_{area}"
        node_sets = [area]
        if index_info["type"] == "project":
            node_sets.append(f"project_{index_info['project_name']}")

        print(f"  Area '{area}': {len(docs)} docs -> dataset '{dataset_name}'")

        if dry_run:
            migrated_this_run += len(docs)
            continue

        for doc_id, doc in docs:
            meta_header = json.dumps(doc.metadata, default=str)
            enriched_text = f"[META:{meta_header}]\n{doc.page_content}"

            try:
                await cognee.add(
                    enriched_text,
                    dataset_name=dataset_name,
                    node_set=node_sets,
                )
                already_migrated.add(doc_id)
                index_state["migrated_doc_ids"] = list(already_migrated)
                migrated_this_run += 1

                if migrated_this_run % 10 == 0:
                    index_state["status"] = "in_progress"
                    state["indices"][index_key] = index_state
                    save_state(base_dir, state)

            except Exception as e:
                error_msg = f"doc {doc_id}: {e}"
                print(f"    ERROR: {error_msg}")
                index_state.setdefault("errors", []).append(error_msg)

    if len(already_migrated) >= len(all_docs):
        index_state["status"] = "complete"
    else:
        index_state["status"] = "partial"

    index_state["migrated_doc_ids"] = list(already_migrated)
    state["indices"][index_key] = index_state
    if not dry_run:
        save_state(base_dir, state)

    knowledge_import_path = os.path.join(db_dir, "knowledge_import.json")
    if os.path.exists(knowledge_import_path) and not dry_run:
        state_dir = os.path.join(base_dir, "usr", "cognee_state", memory_subdir.replace("/", os.sep))
        os.makedirs(state_dir, exist_ok=True)
        shutil.copy2(knowledge_import_path, os.path.join(state_dir, "knowledge_import.json"))
        print(f"  Copied knowledge_import.json to cognee_state")

    return {
        "subdir": memory_subdir,
        "total": len(all_docs),
        "migrated": len(already_migrated),
        "skipped": False,
    }


async def run_cognify(indices: list[dict]):
    import cognee

    datasets = set()
    for index_info in indices:
        dataset_base = subdir_to_dataset(index_info["memory_subdir"])
        for area in ["main", "fragments", "solutions"]:
            datasets.add(f"{dataset_base}_{area}")

    try:
        existing = await cognee.datasets.list_datasets()
        existing_names = {ds.name for ds in existing}
    except Exception:
        existing_names = set()

    datasets_to_cognify = [d for d in datasets if d in existing_names]

    if datasets_to_cognify:
        print(f"\nRunning cognify on {len(datasets_to_cognify)} datasets...")
        try:
            await cognee.cognify(
                datasets=datasets_to_cognify,
                temporal_cognify=True,
            )
            print("  Cognify completed")
        except Exception as e:
            print(f"  Cognify error (non-fatal): {e}")
    else:
        print("\nNo datasets to cognify")


async def verify_migration(indices: list[dict]):
    import cognee
    from cognee import SearchType

    print("\n=== VERIFICATION ===")
    for index_info in indices:
        dataset_base = subdir_to_dataset(index_info["memory_subdir"])
        for area in ["main", "fragments", "solutions"]:
            dataset = f"{dataset_base}_{area}"
            try:
                results = await cognee.search(
                    query_text="test query",
                    query_type=SearchType.CHUNKS,
                    top_k=3,
                    datasets=[dataset],
                )
                count = len(results) if results else 0
                print(f"  {dataset}: {count} results from test search")
            except Exception as e:
                print(f"  {dataset}: search error - {e}")


def backup_completed_indices(indices: list[dict], state: dict):
    for index_info in indices:
        index_key = f"{index_info['type']}:{index_info['memory_subdir']}"
        index_state = state["indices"].get(index_key, {})
        if index_state.get("status") != "complete":
            continue

        if index_info["type"] in ("global_backup",):
            continue

        db_dir = index_info["db_dir"]
        backup_dir = db_dir.rstrip("/") + "_faiss_backup"
        if os.path.exists(db_dir) and not os.path.exists(backup_dir):
            shutil.copytree(db_dir, backup_dir)
            print(f"  Backed up (copy): {db_dir} -> {backup_dir}")


def _migration_looks_empty(state: dict) -> bool:
    """Detect a previous migration that 'completed' with 0 docs (e.g. faiss-cpu was missing)."""
    if not state.get("completed"):
        return False
    for idx_state in state.get("indices", {}).values():
        if idx_state.get("total", 0) > 0:
            return False
    return True


async def run_migration(dry_run: bool = False, verify: bool = False, force: bool = False) -> bool:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(base_dir)

    state = load_state(base_dir)

    if state.get("completed") and not force:
        if _migration_looks_empty(state):
            indices_on_disk = find_faiss_indices(base_dir)
            if indices_on_disk:
                print("Previous migration completed with 0 documents but FAISS indices exist on disk. Re-running...")
                state = {"version": 1, "indices": {}, "completed": False}
                save_state(base_dir, state)
            else:
                await cleanup_backup_datasets(base_dir)
                return True
        else:
            await cleanup_backup_datasets(base_dir)
            return True

    configure_cognee()

    indices = find_faiss_indices(base_dir)
    if not indices:
        state["completed"] = True
        if not dry_run:
            save_state(base_dir, state)
        return True

    print(f"=== FAISS -> Cognee Migration ===")
    print(f"Base dir: {base_dir}")
    if dry_run:
        print("MODE: DRY RUN\n")

    print(f"Found {len(indices)} FAISS indices:")
    for idx in indices:
        print(f"  [{idx['type']}] {idx['memory_subdir']} -> {idx['db_dir']}")

    results = []
    for index_info in indices:
        result = await migrate_index(index_info, state, base_dir, dry_run=dry_run)
        results.append(result)

    print("\n=== MIGRATION SUMMARY ===")
    total_all = sum(r["total"] for r in results)
    migrated_all = sum(r["migrated"] for r in results)
    for r in results:
        status = "SKIP" if r.get("skipped") else "OK"
        print(f"  [{status}] {r['subdir']}: {r['migrated']}/{r['total']} documents")
    print(f"  TOTAL: {migrated_all}/{total_all} documents")

    all_complete = all(
        state["indices"].get(f"{idx['type']}:{idx['memory_subdir']}", {}).get("status") == "complete"
        for idx in indices
    )

    if all_complete and not dry_run:
        state["completed"] = True
        save_state(base_dir, state)

        print("\nBacking up FAISS directories...")
        backup_completed_indices(indices, state)

        await cleanup_backup_datasets(base_dir)

        if verify:
            await run_cognify(indices)
            await verify_migration(indices)

    elif not all_complete and not dry_run:
        partial = [
            r["subdir"] for r in results
            if not r.get("skipped") and r["migrated"] < r["total"]
        ]
        if partial:
            print(f"\nWARNING: Partial migration for: {partial}")
            print("Re-run to continue from where it left off.")

    return all_complete


async def cleanup_backup_datasets(base_dir: str):
    """Remove duplicate datasets created from *_faiss_backup dirs in earlier buggy runs."""
    state = load_state(base_dir)
    if state.get("cleanup_done"):
        return

    try:
        from python.helpers.cognee_init import configure_cognee
        configure_cognee()
        import cognee
        all_datasets = await cognee.datasets.list_datasets()
        backup_datasets = [ds for ds in all_datasets if "_faiss_backup_" in ds.name]
        if not backup_datasets:
            state["cleanup_done"] = True
            save_state(base_dir, state)
            return
        print(f"\nCleaning up {len(backup_datasets)} duplicate backup datasets...")
        for ds in backup_datasets:
            try:
                await cognee.datasets.delete_dataset(ds.id)
                print(f"  Deleted: {ds.name}")
            except Exception as e:
                print(f"  Failed to delete {ds.name}: {e}")
        state["cleanup_done"] = True
        save_state(base_dir, state)
    except Exception as e:
        print(f"  Cleanup error (non-fatal): {e}")


async def main():
    dry_run = "--dry-run" in sys.argv
    verify = "--verify" in sys.argv
    force = "--force" in sys.argv

    success = await run_migration(dry_run=dry_run, verify=verify, force=force)

    if success and "--cleanup" in sys.argv:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        await cleanup_backup_datasets(base_dir)

    print(f"\n{'Done.' if success else 'Migration incomplete -- re-run to continue.'}")


if __name__ == "__main__":
    asyncio.run(main())
