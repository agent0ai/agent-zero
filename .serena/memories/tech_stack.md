# Agent Zero Tech Stack

## Core Technologies
- **Language**: Python (recommended 3.12, works with 3.10-3.13)
- **Framework**: Custom Python framework with Flask for web UI
- **Container**: Docker for runtime environment
- **IDE**: VS Code compatible (VS Code, Cursor, Windsurf)

## Key Python Dependencies
- **AI/ML Libraries**:
  - langchain-core & langchain-community: LLM chain orchestration
  - sentence-transformers: Text embeddings
  - faiss-cpu: Vector database for knowledge base
  - tiktoken: Token counting
  
- **Web & API**:
  - flask[async]: Web framework with async support
  - fastmcp: Model Context Protocol implementation
  - a2wsgi: ASGI/WSGI adapter
  
- **Browser Automation**:
  - browser-use: Browser agent capabilities
  - playwright: Browser automation
  
- **Search & Retrieval**:
  - duckduckgo-search: Web search
  - newspaper3k: Article extraction
  
- **Document Processing**:
  - pypdf: PDF handling
  - pymupdf: Advanced PDF operations
  - pytesseract & pdf2image: OCR capabilities
  - markdownify & html2text: Format conversion
  
- **System Integration**:
  - docker: Container management
  - paramiko: SSH connectivity
  - psutil: System monitoring
  - GitPython: Git operations
  
- **Windows Specific**:
  - pywinpty: Windows pseudo-terminal support

## Model Providers
- Supports multiple LLM providers via configuration
- Chat and utility models configurable separately
- Vision model support available
- Embedding models for knowledge base

## Development Tools
- Error Lens extension for VS Code
- Python debugger integration
- Pre-configured launch.json for debugging