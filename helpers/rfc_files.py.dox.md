# rfc_files.py DOX

## Purpose

- Own the `rfc_files.py` helper module.
- This module exposes RFC-safe filesystem operations.
- Keep this file-level DOX profile synchronized with `rfc_files.py` because this directory is intentionally flat.

## Ownership

- `rfc_files.py` owns the runtime implementation.
- `rfc_files.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Top-level functions:
- `get_abs_path(*relative_paths)`: Convert relative paths to absolute paths based on the base directory.
- `read_file_bin(relative_path: str, backup_dirs=...) -> bytes`: Read binary file content.
- `read_file_base64(relative_path: str, backup_dirs=...) -> str`: Read file content and return as base64 string.
- `write_file_binary(relative_path: str, content: bytes) -> bool`: Write binary content to a file.
- `write_file_base64(relative_path: str, content: str) -> bool`: Write base64 content to a file.
- `delete_file(relative_path: str) -> bool`: Delete a file.
- `delete_directory(relative_path: str) -> bool`: Delete a directory recursively.
- `list_directory(relative_path: str, include_hidden: bool=...) -> list`: List directory contents.
- `make_directories(relative_path: str) -> bool`: Create directories recursively.
- `path_exists(relative_path: str) -> bool`: Check if a path exists.
- `file_exists(relative_path: str) -> bool`: Check if a file exists.
- `folder_exists(relative_path: str) -> bool`: Check if a folder exists.
- `get_subdirectories(relative_path: str, include: str | list[str]=..., exclude: str | list[str] | None=...) -> list[str]`: Get subdirectories in a directory.
- `zip_directory(relative_path: str) -> str`: Create a zip archive of a directory.
- `move_file(source_path: str, destination_path: str) -> bool`: Move a file from source to destination.
- `read_directory_as_zip(relative_path: str) -> bytes`: Read entire directory contents as a zip file.
- `find_file_in_dirs(file_path: str, backup_dirs: list[str]) -> str`: Find a file in the main directory or backup directories.
- `_read_file_binary_impl(file_path: str) -> str`: Implementation function to read a file in binary mode.
- `_write_file_binary_impl(file_path: str, b64_content: str) -> bool`: Implementation function to write binary content to a file.
- `_delete_file_impl(file_path: str) -> bool`: Implementation function to delete a file.
- `_delete_folder_impl(folder_path: str) -> bool`: Implementation function to delete a folder recursively.
- `_list_folder_impl(folder_path: str, include_hidden: bool=...) -> list`: Implementation function to list folder contents.
- `_make_dirs_impl(folder_path: str) -> bool`: Implementation function to create directories.
- `_path_exists_impl(file_path: str) -> bool`: Implementation function to check if path exists.
- `_file_exists_impl(file_path: str) -> bool`: Implementation function to check if file exists.
- `_folder_exists_impl(folder_path: str) -> bool`: Implementation function to check if folder exists.
- `_get_subdirectories_impl(folder_path: str, include: str | list[str], exclude: str | list[str] | None) -> list[str]`: Implementation function to get subdirectories.
- `_zip_dir_impl(folder_path: str) -> str`: Implementation function to create a zip archive of a directory.
- `_move_file_impl(source_path: str, destination_path: str) -> bool`: Implementation function to move a file.
- `_read_directory_impl(dir_path: str) -> str`: Implementation function to zip a directory and return base64 encoded zip.

## Runtime Contracts

- Helper modules own reusable framework APIs and must preserve public callers unless all callers, tests, and docs are updated together.
- Update this file whenever public functions, classes, persistence behavior, path/security assumptions, side effects, or cross-module contracts change.
- Observed side-effect areas: filesystem reads, filesystem writes, filesystem deletion.
- Imported dependency areas include: `base64`, `fnmatch`, `helpers`, `os`, `shutil`, `tempfile`, `zipfile`.

## Key Concepts

- Important called helpers/classes observed in the source: `os.path.abspath`, `os.path.join`, `find_file_in_dirs`, `runtime.call_development_function_sync`, `base64.b64decode`, `get_abs_path`, `base64.b64encode.decode`, `FileNotFoundError`, `os.path.exists`, `os.path.basename`, `os.path.isfile`, `Exception`, `os.makedirs`, `os.remove`, `os.path.isdir`, `shutil.rmtree`, `os.listdir`, `items.sort`, `tempfile.NamedTemporaryFile`, `zipfile.ZipFile`.
- Keep request/response, tool, or helper semantics documented here at the same time as source changes.

## Work Guidance

- Preserve public helper APIs used by core code and plugins unless every caller is updated.
- Keep path, auth, secret, persistence, network, and subprocess behavior explicit and bounded.
- Prefer adding cohesive helper functions here only when behavior is reused across modules.

## Verification

- Run targeted tests for changed helper behavior; run security regressions for auth, filesystem, WebSocket, tunnel, upload, or secret-handling helpers.
- No direct test reference was found by name search; choose the nearest behavioral test or perform a focused smoke check.

## Child DOX Index

No child DOX files.
