# Unified @ Mentions: Files & Chats

Extends the existing `@` repo mention system to support three mention types:
**repos** (existing), **files** (new), and **chats** (new). All three inject
relevant context into the agent's prompt.

---

## Design Decisions

| Decision | Choice |
|----------|--------|
| Trigger | Single `@` with categorized dropdown (tabs: Repos, Files, Chats) |
| File sources | Agent workspace + uploaded local files + files from mentioned GitHub repos |
| File browsing | Search-first with path autocomplete (Cmd+P style) |
| Chat injection | Smart truncation: first 5 + last 10 messages (user/response only) |
| Limits | 10,000 chars per file, 10,000 chars per chat, max 10 total mentions |
| Store | Unified `mentionStore.js` replaces `repoMentionStore.js` |

---

## UI: Categorized Dropdown

When the user types `@`, a dropdown appears with three tabs:

```
+-----------------------------+
|  [Repos]  [Files]  [Chats]  |
|-----------------------------|
|  Search...                  |
|-----------------------------|
|  (filtered results)         |
|  (filtered results)         |
|  (filtered results)         |
+-----------------------------+
```

- Default tab: **Repos** (preserves existing behavior)
- Tabs switch search context; same search box, different data source
- Keyboard: arrow keys navigate results, Tab/click switches tabs, Enter selects,
  Escape closes
- Files tab: results from workspace filesystem + already-mentioned repos' files.
  Small "Upload" button at bottom for local file picker.
- Chats tab: previous chat sessions, searchable by first user message / title.
  Current chat excluded.

Chips below the input distinguish type with icons:
- Repo chips: folder icon + `owner/repo`
- File chips: document icon + truncated path
- Chat chips: chat icon + title preview

---

## Data Flow: Files

### Three sources

**A) Workspace files** — Files tab calls `POST /file_search` with a query string.
Backend does a filename glob, returns:
```json
[{ "path": "/workspace/src/main.py", "source": "workspace", "size": 2450 }]
```

**B) GitHub repo files** — If repos are already mentioned, their file trees
(already fetched) are searchable in the Files tab. Results include repo context:
```json
{ "path": "src/utils.py", "source": "github", "repo": "owner/repo-name" }
```

**C) Uploaded files** — "Upload" button triggers browser `<input type="file">`.
Content read client-side via `FileReader`, stored in mention store. Content
travels with message payload on send.

### Backend injection

Extension `_82_include_file_mentions.py` (hook: `message_loop_prompts_after`):
- Workspace files: reads from filesystem, truncates to 10,000 chars
- GitHub files: fetches raw content via GitHub API, truncates to 10,000 chars
- Uploaded files: content from payload, truncates to 10,000 chars

Template (`prompts/agent.extras.file_mention.md`):
```markdown
# Mentioned File: {{path}}
Source: {{source}}
Language: {{language}}

## Content
{{content}}
```

---

## Data Flow: Chats

### Frontend

Chats tab calls existing chat listing endpoint. Display:
```
"Help me set up the deployment pipeline"   - 2h ago
"Debug the authentication flow"            - yesterday
```
Display text from first user message or stored chat title. Search filters on text.

Mention structure:
```json
{ "context_id": "abc-123", "title": "Help me set up...", "source": "chat" }
```

### Backend injection

Extension `_83_include_chat_mentions.py` (hook: `message_loop_prompts_after`):

1. Loads referenced context's log by `context_id`
2. Filters to `user` and `response` types only (skips tool/agent/progress)
3. Smart truncation:
   - First 5 messages (captures original goal)
   - `... (N messages omitted) ...`
   - Last 10 messages (captures resolution)
4. Total truncated to 10,000 chars

Template (`prompts/agent.extras.chat_mention.md`):
```markdown
# Referenced Chat: {{title}}
Context ID: {{context_id}}

## Conversation
{{messages}}
```

Messages formatted as:
```
**User:** <message text>
**Agent:** <response text>
```

---

## Store Architecture

`repoMentionStore.js` replaced by `mentionStore.js`:

```javascript
{
  // UI state
  isOpen: false,
  activeTab: 'repos',    // 'repos' | 'files' | 'chats'
  searchQuery: '',

  // Data sources (populated on demand)
  repos: [],              // from /github_repos
  files: [],              // from /file_search
  chats: [],              // from existing chat listing

  // Selected mentions (all types, shared array)
  mentions: [],
  // Each: { type: 'repo'|'file'|'chat', ...typeSpecificData }

  // Limits
  maxMentions: 10,
  get remainingSlots() { return this.maxMentions - this.mentions.length; }
}
```

Single `mentions[]` array because:
- Enforces global limit of 10 in one place
- Chips render in insertion order
- `sendMessage()` passes `mentions` — backend sorts by type

localStorage persistence for all types except uploaded file content (too large).

---

## Migration & Backward Compatibility

### Frontend

| Old | New |
|-----|-----|
| `repoMentionStore.js` | `mentionStore.js` |
| `repo-mention-dropdown.html` | `mention-dropdown.html` |
| `repo-mention-chips.html` | `mention-chips.html` |

`chat-bar-input.html` updated to reference new component paths and store name.

### Backend

- `sendMessage()` sends `mentions` instead of `repo_mentions`
- `message.py` accepts both `mentions` (new) and `repo_mentions` (legacy fallback)
- `agent.py` stores under `agent.data['mentions']`
- `_81_include_repo_mentions.py` reads from `mentions` filtered to `type: 'repo'`,
  falls back to `agent.data['repo_mentions']`

### New API endpoint

`POST /file_search` — accepts `{ "query": "string" }`, returns matching file paths
from agent workspace via filename glob.

---

## File Map

### New files

| File | Purpose |
|------|---------|
| `webui/components/chat/input/mentionStore.js` | Unified mention store |
| `webui/components/chat/input/mention-dropdown.html` | Tabbed dropdown |
| `webui/components/chat/input/mention-chips.html` | Type-aware chips |
| `python/api/file_search.py` | Workspace file search endpoint |
| `python/extensions/message_loop_prompts_after/_82_include_file_mentions.py` | File content injection |
| `python/extensions/message_loop_prompts_after/_83_include_chat_mentions.py` | Chat history injection |
| `prompts/agent.extras.file_mention.md` | File mention template |
| `prompts/agent.extras.chat_mention.md` | Chat mention template |

### Modified files

| File | Change |
|------|--------|
| `webui/components/chat/input/chat-bar-input.html` | New component paths, new store |
| `webui/index.js` | `sendMessage()` sends `mentions` |
| `python/api/message.py` | Parse `mentions` with fallback |
| `python/agent.py` | Store `mentions` in `agent.data` |
| `python/extensions/message_loop_prompts_after/_81_include_repo_mentions.py` | Filter from `mentions` |
| `webui/js/messages.js` | Render file/chat indicators |

### Deleted files (after migration)

| File | Replaced by |
|------|-------------|
| `repoMentionStore.js` | `mentionStore.js` |
| `repo-mention-dropdown.html` | `mention-dropdown.html` |
| `repo-mention-chips.html` | `mention-chips.html` |

---

## Implementation Order

1. **Backend**: `file_search.py` endpoint + new extensions + templates
2. **Store**: `mentionStore.js` with all three types
3. **UI**: tabbed dropdown + updated chips
4. **Integration**: wire `sendMessage()`, `message.py`, `agent.py`
5. **Migration**: update `_81`, delete old files
6. **Display**: file/chat indicators in rendered messages
