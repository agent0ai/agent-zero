# Document Query Plugin DOX

## Purpose

- Own document loading, parsing, indexing, and Q&A over local and remote documents.

## Ownership

- `tools/document_query.py` owns the agent-facing query tool.
- The tool logs its message as type `document_query` with an `icon://manage_search Querying: <document>` headline when queries are supplied and `Reading: <document>` without them, naming the first file and appending `+ N more` for multiple documents; `extensions/webui/get_message_handler/` owns the `DOC` badge presentation and `extensions/webui/get_process_step_types/` registers the type.
- Agent-facing error messages render from `prompts/fw.document_query.*.md`, and the Q&A answer streams into the tool log while the model writes it.
- `helpers/` owns fetching, parser routing and query orchestration.
- `helpers/ocr_dependencies.py` owns concurrency-safe, just-in-time installation of legacy OCR system packages.
- `prompts/` owns document-query tool and optimization prompts.
- `hooks.py`, `default_config.yaml`, `plugin.yaml`, `skills/`, `extensions/`, and `webui/` own dependency bootstrap, settings, metadata, skill guidance, hooks, and UI.

## Local Contracts

- Discover the callable through the existing `document-query` skill. The plugin denies it until the skill is loaded in the chat and currently visible. Then ordinary project/profile Tool Access decides. The tool remains in the Tool Access editor.
- The prompt hook withholds the text declaration under inherited policy. Native Responses exposure and dispatch use shared Tool Access. The core compatibility shim checks the bundled gate before execution as well as its normal local policy.
- Respect configured size, timeout, retry, parser concurrency, and OCR limits. The tool accepts destination paths and keys indexed content by its destination and revision. HTTP URLs still use the existing fetch policy.
- `sandbox/index.py` splits and stores chunks and performs native FAISS search in the guest. Each chat supplies its own temporary writable `/index` mount across worker restarts. The framework runs configured embeddings and model calls, and passes vectors without credentials.
- Fetch local and remote resources safely and avoid leaking document contents beyond intended prompt/tool use.
- Parser packages and OCR system dependencies belong only to `sandbox/install.sh` and the guest runtime; host hooks never install them. `helpers/sandbox.py` stages requested document bytes and serves both Document Query and Memory knowledge loaders.
- Keep Tesseract, its Latin language data, and Poppler out of the base image. Install Tesseract immediately before a system-backed image OCR call and add Poppler only for a PDF OCR fallback.
- LiteParse uses its bundled OCR implementation and must not trigger installation of the legacy system OCR packages.
- LiteParse subprocesses use the guest interpreter. Parser source depends only on the standalone `helpers/document.py` value object, standard-library logging and guest packages. First-use installation is outside the document processing deadline; cancellation stops the child sandbox.
- The tool stops its prepared worker on every exit, including cache hits and fetch failures before any parse.

- Create new temporary index directories writable by the document worker at creation and release them with their store.

## Work Guidance

- Coordinate parser changes with timeout handling and fallback behavior.
- Keep on-demand apt work noninteractive, serialized across parser threads, retry-safe around apt locks, and explicit when privilege or package installation fails.
- Keep prompt and skill guidance clear that image files, screenshots, scans, charts, photos, and diagrams should go to vision tools first when available; `document_query` image OCR is a text-focused fallback when vision is unavailable or cannot read the needed text.

## Verification

- Run `tests/test_tool_action_policy.py` for skill gating, saved denials, and shim dispatch. Compare fresh and skill-loaded chats in the text and native Responses surfaces.
- Smoke-test representative PDF, text/HTML, image/OCR, and remote-document queries after parser changes, including first-use OCR installation in a clean runtime image.

## Child DOX Index

No child DOX files.
