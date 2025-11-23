# Agent Zero Code Style and Conventions

## Python Code Style
- **Naming Convention**: snake_case for functions and variables
- **Class Names**: PascalCase (e.g., CodeExecution, MemorySave, AgentConfig)
- **File Organization**: Modular structure with separate directories for tools, helpers, api
- **Private/Internal**: Leading underscore for private methods/variables

## Project Structure Conventions
```
/python/
  /api/        - API endpoints and interfaces
  /extensions/ - Modular extensions
  /helpers/    - Utility functions and support modules
  /tools/      - Tool implementations (one tool per file)
  
/prompts/      - System and tool prompts (markdown files)
/instruments/  - Custom scripts and runtime tools
/knowledge/    - Knowledge base storage
/memory/       - Persistent agent memory
/logs/         - HTML CLI-style chat logs
/webui/        - Web interface components
```

## Tool Development Pattern
- Each tool is a separate Python class in `/python/tools/`
- Tools inherit from base Tool class
- Tools have standardized execute methods
- Disabled tools marked with `._py` extension

## Configuration Management
- Environment variables in `.env` file
- Settings merged from defaults and overrides
- Model configurations use ModelConfig class
- Support for multiple model providers

## Memory and Persistence
- Memory stored in structured format
- Knowledge base uses FAISS vector database
- Projects have isolated memory/knowledge spaces
- Session persistence for chat history

## Testing Approach
- Test files in `/tests/` directory
- Named as `*_test.py` or `test_*.py`
- Unit tests for core components

## Documentation
- Markdown documentation in `/docs/`
- Code visualization with Foam graph
- Inline documentation for complex functions
- Architecture diagrams in SVG format

## Git Workflow
- `.gitignore` excludes virtual environments, logs, temp files
- Memory and knowledge directories tracked but contents ignored
- IDE-specific directories ignored (.cursor/, .windsurf/)

## Error Handling
- Custom exception classes (HandledException, InterventionException)
- Structured error reporting
- User-friendly error messages in UI