## Context7 MCP Integration (Documentation Lookup)

### Overview
You have access to Context7 MCP server for fetching **current, version-specific documentation** for programming libraries. This prevents outdated code patterns and reduces hallucinations.

### When to Use Context7

**USE Context7 when:**
- Working with rapidly-evolving frameworks (Next.js, React, LangChain, FastAPI)
- Unsure about current API syntax or patterns
- User asks about specific library features
- Implementing features where API has changed recently
- Working with multiple libraries that may have version conflicts

**SKIP Context7 when:**
- Writing basic/stable code (standard Python, simple algorithms)
- Working with well-established patterns you're confident about
- User provides specific code examples to follow
- Time-critical tasks where lookup would slow delivery

### Available Tools

#### 1. `resolve-library-id`
Search for libraries and get their Context7 ID.

**Arguments:**
- `query` (string): What you're trying to accomplish
- `libraryName` (string): Library name to search for

**Example:**
```json
{
  "query": "How to create API routes in Next.js",
  "libraryName": "nextjs"
}
```

#### 2. `get-library-docs` / `query-docs`
Fetch documentation for a specific library.

**Arguments:**
- `libraryId` (string): Context7 library ID (e.g., `/vercel/next.js`)
- `query` (string): Specific question about the library

**Example:**
```json
{
  "libraryId": "/vercel/next.js",
  "query": "How to create API routes with authentication"
}
```

### Well-Covered Libraries

| Library | Context7 ID | Snippets | Best For |
|---------|-------------|----------|----------|
| FastAPI | `/websites/fastapi_tiangolo` | 12,277 | Python APIs |
| Next.js | `/vercel/next.js` | 2,055 | React SSR |
| LangChain | `/websites/langchain` | 20,299 | LLM apps |
| pandas | `/websites/pandas_pydata` | 12,746 | Data analysis |
| Django | `/websites/djangoproject_en_6_0` | 10,667 | Python web |
| React | `/facebook/react` | varies | Frontend |

### Workflow Integration

1. **Before implementing** with a modern framework:
   - Quick `resolve-library-id` to confirm library exists
   - `query-docs` for the specific feature you need

2. **During implementation** if stuck:
   - Query for specific error messages or patterns
   - Check for breaking changes between versions

3. **Code review** for best practices:
   - Verify patterns match current recommendations

### Example Development Flow

```
Task: "Build a FastAPI endpoint with JWT auth"

1. resolve-library-id(query="JWT authentication", libraryName="fastapi")
   → Gets /websites/fastapi_tiangolo

2. query-docs(libraryId="/websites/fastapi_tiangolo", query="JWT authentication middleware")
   → Returns current code examples

3. Implement using the returned patterns
```

### Rate Limits
- Do not call either tool more than 3 times per question
- If you can't find what you need after 3 calls, use best available info
- Free tier is sufficient for normal development tasks
