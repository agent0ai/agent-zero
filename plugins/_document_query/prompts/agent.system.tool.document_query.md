### document_query
read, extract, summarize, compare, or answer questions over local/remote documents, PDFs, Office files, HTML/text/code files, large text-heavy files, and fallback OCR when vision tools cannot read a document image/scan.

For document Q&A, document/code analysis, multi-document comparison, PDF or large-file extraction, or fallback OCR after vision tools are unavailable or insufficient, first load the `document-query` skill with `skills_tool:load`, then call this tool using the loaded instructions.

Use vision tools first for image files, screenshots, scans, charts, photos, diagrams, and other visual inputs when available. Call `document_query` for images only as document-style OCR fallback when vision cannot read the needed text.

Minimal args after loading the skill:
- `document`: one local path/URL or a list of paths/URLs
- `queries`: optional list of questions; omit it to return extracted document content

Use normal user-facing language in final answers. Keep parser/runtime details internal.
