# rename_work_dir_file.py DOX

## Purpose

- Own the `rename_work_dir_file.py` API endpoint.
- This module handles workdir file operations for rename work dir file.
- Keep this file-level DOX profile synchronized with `rename_work_dir_file.py` because this directory is intentionally flat.

## Ownership

- `rename_work_dir_file.py` owns the runtime implementation.
- `rename_work_dir_file.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `RenameWorkDirFile` (`ApiHandler`)
  - `async process(self, input: Input, request: Request) -> Output`
- Top-level functions:
- `async rename_item(file_path: str, new_name: str) -> bool`
- `async create_folder(parent_path: str, folder_name: str) -> bool`
- `async move_items(file_paths: list[str], destination_path: str) -> list[str]`

## Runtime Contracts

- Invoke the existing file helpers locally in both development and production; await their async entry points. Path validation, response shapes and mutation hooks remain unchanged.

- HTTP handlers must derive from `helpers.api.ApiHandler`; WebSocket handlers must derive from `helpers.ws.WsHandler`.
- Update this file whenever request payloads, authentication or CSRF requirements, response shapes, route side effects, or WebSocket event contracts change.
- `RenameWorkDirFile` is an `ApiHandler`.
- `RenameWorkDirFile` defines `process(...)`.
- Observed side-effect areas: filesystem writes.
- Imported dependency areas include: `api`, `helpers`, `helpers.api`, `helpers.file_browser`, `posixpath`.

## Key Concepts

- Important called helpers/classes observed in the source: `FileBrowser`, `browser.rename_item`, `browser.create_folder`, `browser.move_items`, `strip`, `posixpath.join`, `file_path.startswith`, `extension.call_extensions_async`, `str.rstrip`, `posixpath.dirname`.
- The `move` action accepts `paths` plus `destinationPath`, emits the standard mutation hook, and returns the refreshed `currentPath` listing used by drag-and-drop clients.
- Keep request/response, tool, or helper semantics documented here at the same time as source changes.

## Work Guidance

- Preserve authentication, CSRF, loopback, and API-key checks unless the endpoint contract explicitly changes.
- Update frontend callers, plugin callers, and tests together when payload shape changes.
- Use `helpers.api.Response` for non-JSON responses, files, redirects, or status-specific replies.

## Verification

- Run endpoint-specific or API/WebSocket tests for changed behavior; smoke-test browser callers when no focused test exists.
- Run `pytest tests/test_file_browser_navigation.py` and smoke-test folder and Up-button drops in the WebUI.

## Child DOX Index

No child DOX files.
