import glob
import os
import hashlib
from typing import Any, Dict, Literal, TypedDict
import csv
import io
from pathlib import Path
from langchain_core.documents import Document
from plugins._document_query.helpers.chunks import split_text
from plugins._document_query.helpers.sandbox import KnowledgeLoader
from helpers.log import LogItem
from helpers.print_style import PrintStyle

def _load_documents(path, ext):
    if ext in {"html", "pdf"}:
        mime = "text/html" if ext == "html" else "application/pdf"
        records = KnowledgeLoader(path, mimetype=mime).load()
    else:
        data = Path(path).read_bytes()
        try:
            text = data.decode("utf-8-sig")
        except UnicodeDecodeError:
            from charset_normalizer import from_bytes
            match = from_bytes(data).best()
            if match is None:
                raise ValueError(f"Cannot decode knowledge file {path}")
            text = str(match)
        if ext == "csv":
            rows = csv.DictReader(io.StringIO(text, newline=""))
            records = [Document(page_content="\n".join(
                f"{key.strip()}: {(value or '').strip()}" for key, value in row.items() if key is not None
            ), metadata={"source": path, "row": i}) for i, row in enumerate(rows)]
        else:
            records = [Document(page_content=text, metadata={"source": path})]
    return [Document(page_content=chunk, metadata=doc.metadata) for doc in records
            for chunk in split_text(doc.page_content)]


class KnowledgeImport(TypedDict):
    file: str
    checksum: str
    ids: list[str]
    state: Literal["changed", "original", "removed"]
    documents: list[Any]


def calculate_checksum(file_path: str) -> str:
    hasher = hashlib.md5()
    with open(file_path, "rb") as f:
        buf = f.read()
        hasher.update(buf)
    return hasher.hexdigest()


def load_knowledge(
    log_item: LogItem | None,
    knowledge_dir: str,
    index: Dict[str, KnowledgeImport],
    metadata: dict[str, Any] = {},
    filename_pattern: str = "**/*",
    recursive: bool = True,
) -> Dict[str, KnowledgeImport]:
    """
    Load knowledge files from a directory with change detection and metadata enhancement.

    This function now includes enhanced error handling and compatibility with the
    intelligent memory consolidation system.
    """

    cnt_files = 0
    cnt_docs = 0

    # Validate and create knowledge directory if needed
    if not knowledge_dir:
        if log_item:
            log_item.stream(progress="\nNo knowledge directory specified")
        PrintStyle(font_color="yellow").print("No knowledge directory specified")
        return index

    if not os.path.exists(knowledge_dir):
        try:
            os.makedirs(knowledge_dir, exist_ok=True)
            # Verify the directory was actually created and is accessible
            if not os.path.exists(knowledge_dir) or not os.access(knowledge_dir, os.R_OK):
                error_msg = f"Knowledge directory {knowledge_dir} was created but is not accessible"
                if log_item:
                    log_item.stream(progress=f"\n{error_msg}")
                PrintStyle(font_color="red").print(error_msg)
                return index

            if log_item:
                log_item.stream(progress=f"\nCreated knowledge directory: {knowledge_dir}")
            PrintStyle(font_color="green").print(f"Created knowledge directory: {knowledge_dir}")
        except (OSError, PermissionError) as e:
            error_msg = f"Failed to create knowledge directory {knowledge_dir}: {e}"
            if log_item:
                log_item.stream(progress=f"\n{error_msg}")
            PrintStyle(font_color="red").print(error_msg)
            return index

    # Final accessibility check for existing directories
    if not os.access(knowledge_dir, os.R_OK):
        error_msg = f"Knowledge directory {knowledge_dir} exists but is not readable"
        if log_item:
            log_item.stream(progress=f"\n{error_msg}")
        PrintStyle(font_color="red").print(error_msg)
        return index

    # Fetch all files in the directory with specified extensions
    try:
        kn_files = glob.glob(os.path.join(knowledge_dir, filename_pattern), recursive=recursive)
        kn_files = [f for f in kn_files if os.path.isfile(f) and not os.path.basename(f).startswith('.')]
    except Exception as e:
        PrintStyle(font_color="red").print(f"Error scanning knowledge directory {knowledge_dir}: {e}")
        if log_item:
            log_item.stream(progress=f"\nError scanning directory: {e}")
        return index

    if kn_files:
        PrintStyle.standard(
            f"Found {len(kn_files)} knowledge files in {knowledge_dir}, processing..."
        )
        if log_item:
            log_item.stream(
                progress=f"\nFound {len(kn_files)} knowledge files in {knowledge_dir}, processing...",
            )

    for file_path in kn_files:
        try:
            # Get file extension safely
            file_parts = os.path.basename(file_path).split('.')
            if len(file_parts) < 2:
                continue  # Skip files without extensions

            ext = file_parts[-1].lower()
            if ext not in {"txt", "md", "json", "csv", "pdf", "html"}:
                continue  # Skip unsupported file types

            checksum = calculate_checksum(file_path)
            if not checksum:
                continue  # Skip files with checksum errors

            file_key = file_path

            # Load existing data from the index or create a new entry
            file_data: KnowledgeImport = index.get(file_key, {
                "file": file_key,
                "checksum": "",
                "ids": [],
                "state": "changed",
                "documents": []
            })

            # Check if file has changed
            if file_data.get("checksum") == checksum:
                file_data["state"] = "original"
            else:
                file_data["state"] = "changed"

            # Process changed files
            if file_data["state"] == "changed":
                try:
                    documents = _load_documents(file_path, ext)
                    file_data["checksum"] = checksum

                    # Enhanced metadata for better consolidation compatibility
                    enhanced_metadata = {
                        **metadata,
                        "source_file": os.path.basename(file_path),
                        "source_path": file_path,
                        "file_type": ext,
                        "knowledge_source": True,  # Flag to distinguish from conversation memories
                        "import_timestamp": None,  # Will be set when inserted into memory
                    }

                    # Apply metadata to all documents
                    for doc in documents:
                        doc.metadata = {**doc.metadata, **enhanced_metadata}

                    file_data["documents"] = documents
                    cnt_files += 1
                    cnt_docs += len(documents)

                except Exception as e:
                    file_data["state"] = "original"
                    PrintStyle(font_color="red").print(f"Error loading {file_path}: {e}")
                    if log_item:
                        log_item.stream(progress=f"\nError loading {os.path.basename(file_path)}: {e}")
                    continue

            # Update the index
            index[file_key] = file_data

        except Exception as e:
            PrintStyle(font_color="red").print(f"Error processing {file_path}: {e}")
            continue

    # Mark removed files
    current_files = set(kn_files)
    for file_key, file_data in list(index.items()):
        if file_key not in current_files and not file_data.get("state"):
            index[file_key]["state"] = "removed"

    # Log results
    if cnt_files > 0 or cnt_docs > 0:
        PrintStyle.standard(f"Processed {cnt_docs} documents from {cnt_files} files.")
        if log_item:
            log_item.stream(
                progress=f"\nProcessed {cnt_docs} documents from {cnt_files} files."
            )

    return index
