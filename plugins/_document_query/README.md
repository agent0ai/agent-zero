# Document Query Plugin

Load, parse, index, and Q&A over local and remote documents with configurable
timeouts and thread-safe parsers.

## Features

- **Strategy-pattern parsers** - MIME-type routing to dedicated parser classes
- **Centralized fetching** - local and HTTP(S) resources are fetched once, size-checked, then passed to parsers
- **LiteParse first path** - fast local parsing for PDFs and supported document/image formats, with legacy fallbacks
- **Adaptive OCR** - long PDFs skip OCR automatically to avoid pathological parse times
- **Adaptive indexing** - very large extracted documents increase chunk size to keep embedding work bounded
- **Bounded parser execution** - sync parsers are offloaded to asyncio.to_thread and globally capped across chats
- **Configurable timeouts** - per-document and gather-level timeouts
- **Expanded format support** - PDF, HTML, text, YAML, XML, TOML, JS, TS, images, and catch-all Unstructured

## Configuration

See default_config.yaml for all options. Key settings:

| Setting | Default | Description |
|---------|---------|-------------|
| fetch_timeout | 30 | HTTP fetch timeout (seconds) |
| fetch_retries | 3 | HTTP retry attempts |
| max_remote_bytes | 52428800 | Max remote document size |
| per_document_timeout | 60 | Max time for a single document parse |
| gather_timeout | 120 | Max time for all documents combined |
| parser_concurrency | 1 | Max parser jobs running across all chats in one process |
| context_intro_chunks | 2 | Leading chunks included per document for title/abstract grounding |
| chunk_size | 1000 | Text splitter chunk size |
| chunk_overlap | 100 | Text splitter overlap |
| max_index_chunks | 1200 | Maximum indexed chunks before adaptive chunk sizing, or 0 for no cap |
| search_threshold | 0.5 | Similarity search threshold |
| liteparse_enabled | true | Prefer LiteParse before legacy parser fallbacks |
| liteparse_num_workers | 2 | Max LiteParse OCR workers per parser job |
| liteparse_ocr_auto_disable_pages | 30 | Disable OCR for PDFs at or above this effective page count |
| thread_offload | true | Offload sync parsers to thread pool |

LiteParse is installed into the Agent Zero framework runtime from hooks.py during
plugin install/startup. If installation fails, the plugin logs the error and
continues with the legacy parser fallbacks.

LiteParse always runs in a child process so native parser and OCR failures stay
isolated from the Web UI process.

## Parsers

| Parser | MIME Types | Backend |
|--------|-----------|---------|
| LiteParseParser | PDF, Office/OpenDocument, images | LiteParse |
| PdfParser | application/pdf | PyMuPDF + Tesseract OCR fallback |
| HtmlParser | text/html | Markdownify transformer |
| TextParser | text/*, application/json, YAML, XML, TOML, JS, TS, shell | Direct read |
| ImageParser | image/* | UnstructuredLoader |
| UnstructuredParser | * (catch-all) | UnstructuredLoader hi-res |

## Adding a new parser

1. Create helpers/parsers/<format>.py extending BaseParser
2. Set mimetypes class attribute
3. Implement _parse_sync(document, config)
4. Register in helpers/parsers/__init__.py
