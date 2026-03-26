# Chat Branching

Create a new chat from any existing point in a conversation.

## What It Does

Adds a **Branch** button to every chat message. Clicking it clones the current chat up to that message, creating a new conversation you can continue independently.

## How It Works

1. **ID-based log ↔ history linking**
   Every `LogItem` and `history.Message` share a UUID generated at creation time. The branch button is only shown on messages that carry this ID.

2. **Clone & trim**
   - Serializes the source context → deserializes into a new context with a fresh ID.
   - Walks log entries: keeps everything up to the selected `log_no`, discards the rest.
   - Collects the IDs of kept entries and uses them to trim `history.messages` so log and history stay consistent.

3. **Persist & refresh**
   - Saves the branched chat immediately.
   - Marks UI state dirty so all connected tabs see the new branch.

## Entry Points

| Path | Purpose |
|---|---|
| `api/branch_chat.py` | API endpoint — clone, trim, persist |
| `extensions/webui/set_messages_after_loop/inject-branch-buttons.js` | Injects the Branch button into each message DOM element |

## Plugin Metadata

- **Name**: `_chat_branching`
- **Title**: `Chat Branching`
- **Description**: Branch a chat from any message, creating a new chat with history up to that point.
