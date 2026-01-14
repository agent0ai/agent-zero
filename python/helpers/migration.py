import os
from python.helpers import files
from python.helpers.print_style import PrintStyle

def migrate_user_data() -> None:
    """
    Migrate user data from /tmp and other locations to /usr.
    """
    
    PrintStyle().print("Checking for data migration...")
    
    # --- Migrate Directories -------------------------------------------------------
    # Move directories from tmp/ or other source locations to usr/
    
    _move_dir("tmp/chats", "usr/chats")
    _move_dir("tmp/scheduler", "usr/scheduler")
    _move_dir("tmp/uploads", "usr/uploads")
    _move_dir("tmp/upload", "usr/upload")
    _move_dir("tmp/downloads", "usr/downloads")
    _move_dir("tmp/email", "usr/email")
    _move_dir("knowledge/custom", "usr/knowledge")
    _move_dir("instruments/custom", "usr/instruments")

    # --- Migrate Files -------------------------------------------------------------
    # Move specific configuration files to usr/
    
    _move_file("tmp/settings.json", "usr/settings.json")
    _move_file("tmp/secrets.env", "usr/secrets.env")
    _move_file(".env", "usr/.env")

    # --- Special Migration Cases ---------------------------------------------------
    
    # Migrate Memory
    _migrate_memory()

    # Flatten default directories (knowledge/default -> knowledge/, etc.)
    # We use _merge_dir_contents because we want to move the *contents* of default/ 
    # into the parent directory, not move the default directory itself.
    _merge_dir_contents("knowledge/default", "knowledge")
    _merge_dir_contents("instruments/default", "instruments")

    # --- Cleanup -------------------------------------------------------------------
    
    # Remove obsolete directories after migration
    _cleanup_obsolete()

    PrintStyle().print("Migration check complete.")

# --- Helper Functions ----------------------------------------------------------

def _move_dir(src: str, dst: str) -> None:
    """
    Move a directory from src to dst if src exists and dst does not.
    """
    if files.exists(src) and not files.exists(dst):
        PrintStyle().print(f"Migrating {src} to {dst}...")
        files.move_dir(src, dst)

def _move_file(src: str, dst: str) -> None:
    """
    Move a file from src to dst if src exists and dst does not.
    """
    if files.exists(src) and not files.exists(dst):
        PrintStyle().print(f"Migrating {src} to {dst}...")
        files.move_file(src, dst)

def _migrate_memory(base_path: str = "memory") -> None:
    """
    Migrate memory subdirectories.
    """
    subdirs = files.get_subdirectories(base_path)
    for subdir in subdirs:
        if subdir == "embeddings":
            # Special case: Embeddings
            _move_dir("memory/embeddings", "tmp/memory/embeddings")
        else:
            # Move other memory items to usr/memory
            dst = f"usr/memory/{subdir}"
            _move_dir(f"memory/{subdir}", dst)

def _merge_dir_contents(src_parent: str, dst_parent: str) -> None:
    """
    Moves all subdirectories from src_parent to dst_parent.
    Useful for flattening structures like 'knowledge/default/*' -> 'knowledge/*'.
    """
    if not files.exists(src_parent):
        return

    # Iterate over subdirectories in the source parent
    subdirs = files.get_subdirectories(src_parent)
    for subdir in subdirs:
        src = f"{src_parent}/{subdir}"
        dst = f"{dst_parent}/{subdir}"
        
        # Move the subdirectory if it doesn't exist in destination
        _move_dir(src, dst)

def _cleanup_obsolete() -> None:
    """
    Remove directories that are no longer needed.
    """
    to_remove = [
        "knowledge/default",
        "instruments/default",
        "memory"
    ]
    for path in to_remove:
        if files.exists(path):
            PrintStyle().print(f"Removing {path}...")
            files.delete_dir(path)
