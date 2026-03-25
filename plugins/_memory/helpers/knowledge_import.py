import glob
import os
import hashlib
from pathlib import Path
from typing import Any, Dict, Literal, TypedDict
from langchain_community.document_loaders import (
    CSVLoader,
    PyPDFLoader,
    TextLoader,
    UnstructuredHTMLLoader,
)
from langchain_core.documents import Document
from helpers.log import LogItem
from helpers.print_style import PrintStyle
from helpers import yaml as yaml_helper

text_loader_kwargs = {"autodetect_encoding": True}


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

    # Mapping file extensions to corresponding loader classes
    # Note: Using TextLoader for JSON and MD to avoid parsing issues with consolidation
    file_types_loaders = {
        "txt": TextLoader,
        "pdf": PyPDFLoader,
        "csv": CSVLoader,
        "html": UnstructuredHTMLLoader,
        "json": TextLoader,  # Use TextLoader for better consolidation compatibility
        "md": TextLoader,    # Use TextLoader for better consolidation compatibility
    }

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
            if ext not in file_types_loaders:
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
                file_data["checksum"] = checksum
                autodream_metadata: dict[str, Any] = {}

                try:
                    if ext == "md" and metadata.get("autodream_source"):
                        documents, autodream_metadata = (
                            load_autodream_markdown_documents(file_path)
                        )
                    else:
                        loader_cls = file_types_loaders[ext]
                        loader = loader_cls(
                            file_path,
                            **(
                                text_loader_kwargs
                                if ext in ["txt", "csv", "html", "md"]
                                else {}
                            ),
                        )
                        documents = loader.load_and_split()

                    # Enhanced metadata for better consolidation compatibility
                    enhanced_metadata = {
                        **metadata,
                        "source_file": os.path.basename(file_path),
                        "source_path": file_path,
                        "file_type": ext,
                        "knowledge_source": metadata.get(
                            "knowledge_source", True
                        ),  # File-backed by default, but callers may override.
                        "import_timestamp": None,  # Will be set when inserted into memory
                        **autodream_metadata,
                    }

                    # Apply metadata to all documents
                    for doc in documents:
                        doc.metadata = {**doc.metadata, **enhanced_metadata}

                    file_data["documents"] = documents
                    cnt_files += 1
                    cnt_docs += len(documents)

                except Exception as e:
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


def load_autodream_markdown_documents(
    file_path: str,
) -> tuple[list[Document], dict[str, Any]]:
    text = Path(file_path).read_text(encoding="utf-8")
    frontmatter, body = parse_markdown_frontmatter(text)
    metadata = extract_autodream_frontmatter_metadata(frontmatter)
    page_content = body.strip() or text.strip()
    return [Document(page_content=page_content, metadata={})], metadata


def parse_markdown_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    lines = text.splitlines()
    if len(lines) >= 3 and lines[0].strip() == "---":
        end_index = -1
        for i, line in enumerate(lines[1:], start=1):
            if line.strip() == "---":
                end_index = i
                break
        if end_index > 0:
            metadata_text = "\n".join(lines[1:end_index])
            body_text = "\n".join(lines[end_index + 1 :]).strip()
            metadata = yaml_helper.loads(metadata_text) or {}
            if isinstance(metadata, dict):
                return metadata, body_text
    return {}, text.strip()


def extract_autodream_frontmatter_metadata(frontmatter: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(frontmatter, dict):
        return {}

    metadata: dict[str, Any] = {"autodream_file": True}
    for key in [
        "title",
        "description",
        "updated_at",
        "grounding",
        "memory_scope",
        "canonical_scope_name",
        "project_title",
    ]:
        value = frontmatter.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if text:
            metadata[key] = text

    for key in ["source_context_ids", "source_first_prompts", "source_memory_ids"]:
        value = frontmatter.get(key)
        if not isinstance(value, list):
            continue
        normalized = [str(item).strip() for item in value if str(item).strip()]
        if normalized:
            metadata[key] = normalized

    return metadata
